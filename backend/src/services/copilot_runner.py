"""
Subprocess runner for GitHub Copilot CLI integration.

Provides:
- Subprocess spawning with token injection
- Stdout/stderr capture with line-by-line parsing
- Timeout handling
- Error handling and cleanup
"""

import asyncio
import logging
import os
import signal
from typing import Optional, Callable, List, AsyncIterator
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class SubprocessError(Exception):
    """Base exception for subprocess errors."""
    pass


class SubprocessTimeoutError(SubprocessError):
    """Raised when subprocess exceeds timeout."""
    pass


class SubprocessExecutionError(SubprocessError):
    """Raised when subprocess fails to execute."""
    pass


@dataclass
class SubprocessResult:
    """Result of subprocess execution."""
    return_code: int
    stdout: str
    stderr: str
    timed_out: bool
    execution_time: float  # seconds


class CopilotRunner:
    """
    Runner for GitHub Copilot CLI subprocess operations.
    
    Handles:
    - Subprocess spawning with environment variables
    - Real-time stdout/stderr streaming
    - Timeout enforcement
    - Graceful termination and cleanup
    """
    
    # Default timeout (5 minutes)
    DEFAULT_TIMEOUT_SECONDS = 300
    
    # Copilot CLI command paths
    COPILOT_CLI_PATH = "gh"  # Assumes 'gh' in PATH
    
    def __init__(self, timeout_seconds: Optional[int] = None):
        """
        Initialize Copilot runner.
        
        Args:
            timeout_seconds: Maximum execution time (default: 300 seconds)
        """
        self.timeout_seconds = timeout_seconds or self.DEFAULT_TIMEOUT_SECONDS
        self._running_processes: List[asyncio.subprocess.Process] = []
    
    async def run_command(
        self,
        args: List[str],
        github_token: str,
        working_dir: Optional[str] = None,
        env: Optional[dict] = None,
        on_stdout: Optional[Callable[[str], None]] = None,
        on_stderr: Optional[Callable[[str], None]] = None
    ) -> SubprocessResult:
        """
        Run Copilot CLI command as subprocess.
        
        Args:
            args: Command arguments (e.g., ['copilot', 'suggest', '--help'])
            github_token: GitHub personal access token
            working_dir: Working directory for subprocess
            env: Additional environment variables
            on_stdout: Callback for stdout lines (real-time)
            on_stderr: Callback for stderr lines (real-time)
        
        Returns:
            SubprocessResult with execution details
        
        Raises:
            SubprocessTimeoutError: If execution exceeds timeout
            SubprocessExecutionError: If subprocess fails to start or crashes
        """
        import time
        start_time = time.time()
        
        # Prepare environment
        process_env = os.environ.copy()
        
        # Inject GitHub token
        process_env["GITHUB_TOKEN"] = github_token
        process_env["GH_TOKEN"] = github_token
        
        # Add custom environment variables
        if env:
            process_env.update(env)
        
        # Prepare command
        command = [self.COPILOT_CLI_PATH] + args
        
        logger.info(f"Running command: {' '.join(command)}")
        
        try:
            # Start subprocess
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=process_env,
                cwd=working_dir
            )
            
            self._running_processes.append(process)
            
            # Capture stdout/stderr with timeout
            stdout_lines = []
            stderr_lines = []
            
            try:
                # Run with timeout
                stdout_data, stderr_data = await asyncio.wait_for(
                    self._capture_output(
                        process,
                        stdout_lines,
                        stderr_lines,
                        on_stdout,
                        on_stderr
                    ),
                    timeout=self.timeout_seconds
                )
                
                # Wait for process to complete
                await process.wait()
                
                execution_time = time.time() - start_time
                
                result = SubprocessResult(
                    return_code=process.returncode or 0,
                    stdout="\n".join(stdout_lines),
                    stderr="\n".join(stderr_lines),
                    timed_out=False,
                    execution_time=execution_time
                )
                
                logger.info(f"Command completed in {execution_time:.2f}s with return code {result.return_code}")
                return result
            
            except asyncio.TimeoutError:
                logger.warning(f"Command timed out after {self.timeout_seconds}s")
                
                # Kill process
                await self._terminate_process(process)
                
                execution_time = time.time() - start_time
                
                result = SubprocessResult(
                    return_code=-1,
                    stdout="\n".join(stdout_lines),
                    stderr="\n".join(stderr_lines) + "\n[Process terminated due to timeout]",
                    timed_out=True,
                    execution_time=execution_time
                )
                
                raise SubprocessTimeoutError(
                    f"Command timed out after {self.timeout_seconds} seconds"
                )
            
            finally:
                # Cleanup
                if process in self._running_processes:
                    self._running_processes.remove(process)
        
        except FileNotFoundError:
            logger.error(f"Command not found: {command[0]}")
            raise SubprocessExecutionError(f"Command not found: {command[0]}")
        
        except Exception as e:
            logger.error(f"Subprocess execution failed: {e}")
            raise SubprocessExecutionError(f"Subprocess execution failed: {str(e)}")
    
    async def run_command_streaming(
        self,
        args: List[str],
        github_token: str,
        working_dir: Optional[str] = None,
        env: Optional[dict] = None
    ) -> AsyncIterator[tuple[str, str]]:
        """
        Run command with streaming output.
        
        Args:
            args: Command arguments
            github_token: GitHub PAT
            working_dir: Working directory
            env: Additional environment variables
        
        Yields:
            Tuples of (stream_type, line) where stream_type is 'stdout' or 'stderr'
        
        Raises:
            SubprocessTimeoutError: If execution exceeds timeout
            SubprocessExecutionError: If subprocess fails
        """
        import time
        start_time = time.time()
        
        # Prepare environment
        process_env = os.environ.copy()
        process_env["GITHUB_TOKEN"] = github_token
        process_env["GH_TOKEN"] = github_token
        
        if env:
            process_env.update(env)
        
        # Prepare command
        command = [self.COPILOT_CLI_PATH] + args
        
        logger.info(f"Running streaming command: {' '.join(command)}")
        
        try:
            # Start subprocess
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=process_env,
                cwd=working_dir
            )
            
            self._running_processes.append(process)
            
            try:
                # Stream output with timeout
                async for stream_type, line in self._stream_output_with_timeout(
                    process,
                    self.timeout_seconds
                ):
                    yield stream_type, line
                
                # Wait for process to complete
                await process.wait()
                
                execution_time = time.time() - start_time
                logger.info(f"Streaming command completed in {execution_time:.2f}s")
            
            except asyncio.TimeoutError:
                logger.warning(f"Streaming command timed out after {self.timeout_seconds}s")
                await self._terminate_process(process)
                raise SubprocessTimeoutError(f"Command timed out after {self.timeout_seconds} seconds")
            
            finally:
                if process in self._running_processes:
                    self._running_processes.remove(process)
        
        except FileNotFoundError:
            raise SubprocessExecutionError(f"Command not found: {command[0]}")
        except Exception as e:
            raise SubprocessExecutionError(f"Subprocess execution failed: {str(e)}")
    
    async def _capture_output(
        self,
        process: asyncio.subprocess.Process,
        stdout_lines: List[str],
        stderr_lines: List[str],
        on_stdout: Optional[Callable[[str], None]],
        on_stderr: Optional[Callable[[str], None]]
    ) -> tuple[bytes, bytes]:
        """Capture subprocess output line-by-line."""
        
        async def read_stream(stream, lines_list, callback):
            """Read stream line by line."""
            if stream is None:
                return b""
            
            data = []
            while True:
                line = await stream.readline()
                if not line:
                    break
                
                line_str = line.decode('utf-8', errors='replace').rstrip()
                lines_list.append(line_str)
                data.append(line)
                
                # Call callback for real-time processing
                if callback:
                    callback(line_str)
            
            return b"".join(data)
        
        # Read both streams concurrently
        stdout_task = asyncio.create_task(
            read_stream(process.stdout, stdout_lines, on_stdout)
        )
        stderr_task = asyncio.create_task(
            read_stream(process.stderr, stderr_lines, on_stderr)
        )
        
        stdout_data = await stdout_task
        stderr_data = await stderr_task
        
        return stdout_data, stderr_data
    
    async def _stream_output_with_timeout(
        self,
        process: asyncio.subprocess.Process,
        timeout: float
    ) -> AsyncIterator[tuple[str, str]]:
        """Stream output with timeout enforcement."""
        
        async def read_stdout():
            """Read stdout lines."""
            if process.stdout is None:
                return
            
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                yield "stdout", line.decode('utf-8', errors='replace').rstrip()
        
        async def read_stderr():
            """Read stderr lines."""
            if process.stderr is None:
                return
            
            while True:
                line = await process.stderr.readline()
                if not line:
                    break
                yield "stderr", line.decode('utf-8', errors='replace').rstrip()
        
        # Merge streams
        stdout_gen = read_stdout()
        stderr_gen = read_stderr()
        
        # Use asyncio.gather to read both streams
        pending = {
            asyncio.create_task(stdout_gen.__anext__()): "stdout",
            asyncio.create_task(stderr_gen.__anext__()): "stderr"
        }
        
        import time
        deadline = time.time() + timeout
        
        while pending:
            # Check timeout
            remaining = deadline - time.time()
            if remaining <= 0:
                raise asyncio.TimeoutError()
            
            # Wait for next line from either stream
            done, pending_set = await asyncio.wait(
                pending.keys(),
                timeout=min(remaining, 0.1),
                return_when=asyncio.FIRST_COMPLETED
            )
            
            for task in done:
                stream_type = pending.pop(task)
                
                try:
                    result = task.result()
                    yield result
                    
                    # Create new task for next line
                    if stream_type == "stdout":
                        new_task = asyncio.create_task(stdout_gen.__anext__())
                    else:
                        new_task = asyncio.create_task(stderr_gen.__anext__())
                    
                    pending[new_task] = stream_type
                
                except StopAsyncIteration:
                    # Stream ended
                    pass
    
    async def _terminate_process(self, process: asyncio.subprocess.Process):
        """Gracefully terminate subprocess."""
        if process.returncode is not None:
            return  # Already terminated
        
        try:
            # Try graceful termination first
            process.terminate()
            
            # Wait up to 5 seconds for graceful shutdown
            try:
                await asyncio.wait_for(process.wait(), timeout=5.0)
                logger.info("Process terminated gracefully")
            except asyncio.TimeoutError:
                # Force kill
                process.kill()
                await process.wait()
                logger.warning("Process killed forcefully")
        
        except ProcessLookupError:
            # Process already dead
            pass
    
    async def cancel_all(self):
        """Cancel all running processes."""
        logger.info(f"Cancelling {len(self._running_processes)} running processes")
        
        for process in list(self._running_processes):
            await self._terminate_process(process)
        
        self._running_processes.clear()
    
    def get_running_count(self) -> int:
        """Get count of currently running processes."""
        return len(self._running_processes)


# Global runner instance
copilot_runner = CopilotRunner()
