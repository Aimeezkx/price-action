"""
Resource Exhaustion Testing Utilities

This module provides utilities for testing system behavior under resource constraints
including memory, disk space, CPU, and database connections.

Requirements covered: 6.4 - System resource exhaustion handling
"""

import asyncio
import psutil
import tempfile
import os
import shutil
import threading
import time
from contextlib import contextmanager
from unittest.mock import patch, MagicMock
from typing import Dict, Any, List, Optional, Callable
import gc
import sys


class ResourceMonitor:
    """Monitor system resource usage"""
    
    def __init__(self):
        self.memory_samples = []
        self.cpu_samples = []
        self.disk_samples = []
        self.monitoring = False
        
    def start_monitoring(self, interval: float = 1.0):
        """Start monitoring system resources"""
        self.monitoring = True
        self.memory_samples = []
        self.cpu_samples = []
        self.disk_samples = []
        
        def monitor():
            while self.monitoring:
                try:
                    # Memory usage
                    memory = psutil.virtual_memory()
                    self.memory_samples.append({
                        'timestamp': time.time(),
                        'percent': memory.percent,
                        'available': memory.available,
                        'used': memory.used
                    })
                    
                    # CPU usage
                    cpu_percent = psutil.cpu_percent(interval=None)
                    self.cpu_samples.append({
                        'timestamp': time.time(),
                        'percent': cpu_percent
                    })
                    
                    # Disk usage
                    disk = psutil.disk_usage('/')
                    self.disk_samples.append({
                        'timestamp': time.time(),
                        'percent': (disk.used / disk.total) * 100,
                        'free': disk.free,
                        'used': disk.used
                    })
                    
                    time.sleep(interval)
                except Exception:
                    break
        
        self.monitor_thread = threading.Thread(target=monitor, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring system resources"""
        self.monitoring = False
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join(timeout=2.0)
    
    def get_peak_usage(self) -> Dict[str, Any]:
        """Get peak resource usage during monitoring"""
        peak_memory = max(self.memory_samples, key=lambda x: x['percent'])['percent'] if self.memory_samples else 0
        peak_cpu = max(self.cpu_samples, key=lambda x: x['percent'])['percent'] if self.cpu_samples else 0
        peak_disk = max(self.disk_samples, key=lambda x: x['percent'])['percent'] if self.disk_samples else 0
        
        return {
            'memory_percent': peak_memory,
            'cpu_percent': peak_cpu,
            'disk_percent': peak_disk
        }
    
    def get_average_usage(self) -> Dict[str, Any]:
        """Get average resource usage during monitoring"""
        avg_memory = sum(s['percent'] for s in self.memory_samples) / len(self.memory_samples) if self.memory_samples else 0
        avg_cpu = sum(s['percent'] for s in self.cpu_samples) / len(self.cpu_samples) if self.cpu_samples else 0
        avg_disk = sum(s['percent'] for s in self.disk_samples) / len(self.disk_samples) if self.disk_samples else 0
        
        return {
            'memory_percent': avg_memory,
            'cpu_percent': avg_cpu,
            'disk_percent': avg_disk
        }


class MemoryExhaustionSimulator:
    """Simulate memory exhaustion scenarios"""
    
    def __init__(self):
        self.allocated_memory = []
        
    @contextmanager
    def simulate_memory_pressure(self, target_usage_percent: float = 90.0):
        """Simulate high memory usage"""
        try:
            # Get current memory info
            memory = psutil.virtual_memory()
            current_usage = memory.percent
            
            if current_usage < target_usage_percent:
                # Calculate how much memory to allocate
                target_bytes = (target_usage_percent - current_usage) / 100 * memory.total
                chunk_size = min(target_bytes, 100 * 1024 * 1024)  # 100MB chunks
                
                # Allocate memory in chunks
                while psutil.virtual_memory().percent < target_usage_percent:
                    try:
                        chunk = bytearray(int(chunk_size))
                        self.allocated_memory.append(chunk)
                        time.sleep(0.1)  # Small delay to avoid system freeze
                    except MemoryError:
                        break
            
            yield psutil.virtual_memory().percent
            
        finally:
            # Clean up allocated memory
            self.allocated_memory.clear()
            gc.collect()
    
    @contextmanager
    def simulate_memory_leak(self, leak_rate: int = 1024 * 1024):  # 1MB per second
        """Simulate gradual memory leak"""
        leak_data = []
        leak_active = True
        
        def leak_memory():
            while leak_active:
                try:
                    chunk = bytearray(leak_rate)
                    leak_data.append(chunk)
                    time.sleep(1.0)
                except MemoryError:
                    break
        
        leak_thread = threading.Thread(target=leak_memory, daemon=True)
        leak_thread.start()
        
        try:
            yield
        finally:
            leak_active = False
            leak_data.clear()
            gc.collect()
    
    def get_memory_info(self) -> Dict[str, Any]:
        """Get current memory information"""
        memory = psutil.virtual_memory()
        return {
            'total': memory.total,
            'available': memory.available,
            'percent': memory.percent,
            'used': memory.used,
            'free': memory.free
        }


class DiskSpaceSimulator:
    """Simulate disk space exhaustion scenarios"""
    
    def __init__(self):
        self.temp_files = []
        self.temp_dir = None
        
    @contextmanager
    def simulate_disk_full(self, target_usage_percent: float = 95.0, test_path: str = None):
        """Simulate disk space exhaustion"""
        if test_path is None:
            self.temp_dir = tempfile.mkdtemp()
            test_path = self.temp_dir
        
        try:
            # Get current disk usage
            disk = psutil.disk_usage(test_path)
            current_usage = (disk.used / disk.total) * 100
            
            if current_usage < target_usage_percent:
                # Calculate how much space to fill
                target_bytes = ((target_usage_percent - current_usage) / 100) * disk.total
                
                # Create large files to fill disk space
                file_count = 0
                bytes_written = 0
                
                while bytes_written < target_bytes:
                    try:
                        file_path = os.path.join(test_path, f'fill_file_{file_count}.tmp')
                        chunk_size = min(target_bytes - bytes_written, 100 * 1024 * 1024)  # 100MB chunks
                        
                        with open(file_path, 'wb') as f:
                            f.write(b'0' * int(chunk_size))
                        
                        self.temp_files.append(file_path)
                        bytes_written += chunk_size
                        file_count += 1
                        
                        # Check if we've reached the target
                        current_disk = psutil.disk_usage(test_path)
                        current_usage = (current_disk.used / current_disk.total) * 100
                        if current_usage >= target_usage_percent:
                            break
                            
                    except OSError:
                        # Disk is full
                        break
            
            yield psutil.disk_usage(test_path)
            
        finally:
            # Clean up temporary files
            for file_path in self.temp_files:
                try:
                    os.remove(file_path)
                except OSError:
                    pass
            
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir, ignore_errors=True)
            
            self.temp_files.clear()
    
    @contextmanager
    def simulate_slow_disk_io(self, delay_per_operation: float = 0.1):
        """Simulate slow disk I/O operations"""
        original_open = open
        
        def slow_open(*args, **kwargs):
            time.sleep(delay_per_operation)
            return original_open(*args, **kwargs)
        
        with patch('builtins.open', side_effect=slow_open):
            yield
    
    def get_disk_info(self, path: str = '/') -> Dict[str, Any]:
        """Get current disk space information"""
        disk = psutil.disk_usage(path)
        return {
            'total': disk.total,
            'used': disk.used,
            'free': disk.free,
            'percent': (disk.used / disk.total) * 100
        }


class CPULoadSimulator:
    """Simulate high CPU load scenarios"""
    
    def __init__(self):
        self.load_threads = []
        self.load_active = False
        
    @contextmanager
    def simulate_cpu_load(self, target_usage_percent: float = 95.0, duration: float = 10.0):
        """Simulate high CPU usage"""
        self.load_active = True
        cpu_count = psutil.cpu_count()
        
        # Calculate how many threads to use based on target usage
        threads_needed = max(1, int((target_usage_percent / 100) * cpu_count))
        
        def cpu_intensive_task():
            end_time = time.time() + duration
            while self.load_active and time.time() < end_time:
                # CPU-intensive calculation
                for _ in range(10000):
                    _ = sum(i * i for i in range(100))
        
        # Start CPU load threads
        for _ in range(threads_needed):
            thread = threading.Thread(target=cpu_intensive_task, daemon=True)
            thread.start()
            self.load_threads.append(thread)
        
        try:
            yield
        finally:
            self.load_active = False
            
            # Wait for threads to finish
            for thread in self.load_threads:
                thread.join(timeout=1.0)
            
            self.load_threads.clear()
    
    @contextmanager
    def simulate_cpu_spikes(self, spike_duration: float = 1.0, interval: float = 5.0, total_duration: float = 30.0):
        """Simulate intermittent CPU spikes"""
        self.load_active = True
        
        def spike_generator():
            end_time = time.time() + total_duration
            
            while self.load_active and time.time() < end_time:
                # Create CPU spike
                spike_end = time.time() + spike_duration
                while self.load_active and time.time() < spike_end:
                    for _ in range(10000):
                        _ = sum(i * i for i in range(100))
                
                # Rest period
                time.sleep(interval)
        
        spike_thread = threading.Thread(target=spike_generator, daemon=True)
        spike_thread.start()
        
        try:
            yield
        finally:
            self.load_active = False
            spike_thread.join(timeout=2.0)
    
    def get_cpu_info(self) -> Dict[str, Any]:
        """Get current CPU information"""
        return {
            'percent': psutil.cpu_percent(interval=1),
            'count': psutil.cpu_count(),
            'freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
            'load_avg': os.getloadavg() if hasattr(os, 'getloadavg') else None
        }


class DatabaseConnectionSimulator:
    """Simulate database connection exhaustion"""
    
    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self.active_connections = []
        self.connection_count = 0
        
    @contextmanager
    def simulate_connection_exhaustion(self):
        """Simulate database connection pool exhaustion"""
        # Fill up connection pool
        for i in range(self.max_connections):
            connection = MagicMock()
            connection.id = f"conn_{i}"
            self.active_connections.append(connection)
        
        def mock_get_connection():
            if len(self.active_connections) >= self.max_connections:
                raise Exception("Connection pool exhausted")
            
            connection = MagicMock()
            connection.id = f"conn_{len(self.active_connections)}"
            self.active_connections.append(connection)
            return connection
        
        def mock_release_connection(connection):
            if connection in self.active_connections:
                self.active_connections.remove(connection)
        
        try:
            with patch('app.core.database.get_connection', side_effect=mock_get_connection), \
                 patch('app.core.database.release_connection', side_effect=mock_release_connection):
                yield
        finally:
            self.active_connections.clear()
    
    @contextmanager
    def simulate_slow_queries(self, query_delay: float = 2.0):
        """Simulate slow database queries"""
        def slow_query(*args, **kwargs):
            time.sleep(query_delay)
            return MagicMock()
        
        with patch('app.core.database.execute_query', side_effect=slow_query):
            yield
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get current connection pool information"""
        return {
            'active_connections': len(self.active_connections),
            'max_connections': self.max_connections,
            'available_connections': self.max_connections - len(self.active_connections)
        }


class ResourceExhaustionTester:
    """Main class for testing resource exhaustion scenarios"""
    
    def __init__(self):
        self.monitor = ResourceMonitor()
        self.memory_simulator = MemoryExhaustionSimulator()
        self.disk_simulator = DiskSpaceSimulator()
        self.cpu_simulator = CPULoadSimulator()
        self.db_simulator = DatabaseConnectionSimulator()
        
    async def test_memory_exhaustion_handling(self, operation: Callable) -> Dict[str, Any]:
        """Test operation behavior under memory pressure"""
        results = {}
        
        # Test normal operation first
        self.monitor.start_monitoring()
        try:
            start_time = time.time()
            await operation() if asyncio.iscoroutinefunction(operation) else operation()
            results['normal'] = {
                'status': 'success',
                'duration': time.time() - start_time,
                'peak_memory': self.monitor.get_peak_usage()['memory_percent']
            }
        except Exception as e:
            results['normal'] = {'status': 'failure', 'error': str(e)}
        finally:
            self.monitor.stop_monitoring()
        
        # Test under memory pressure
        with self.memory_simulator.simulate_memory_pressure(90.0):
            self.monitor.start_monitoring()
            try:
                start_time = time.time()
                await operation() if asyncio.iscoroutinefunction(operation) else operation()
                results['memory_pressure'] = {
                    'status': 'success',
                    'duration': time.time() - start_time,
                    'peak_memory': self.monitor.get_peak_usage()['memory_percent']
                }
            except Exception as e:
                results['memory_pressure'] = {'status': 'failure', 'error': str(e)}
            finally:
                self.monitor.stop_monitoring()
        
        return results
    
    async def test_disk_exhaustion_handling(self, operation: Callable) -> Dict[str, Any]:
        """Test operation behavior when disk space is low"""
        results = {}
        
        # Test normal operation
        try:
            start_time = time.time()
            await operation() if asyncio.iscoroutinefunction(operation) else operation()
            results['normal'] = {
                'status': 'success',
                'duration': time.time() - start_time,
                'disk_usage': self.disk_simulator.get_disk_info()['percent']
            }
        except Exception as e:
            results['normal'] = {'status': 'failure', 'error': str(e)}
        
        # Test with low disk space
        with self.disk_simulator.simulate_disk_full(95.0):
            try:
                start_time = time.time()
                await operation() if asyncio.iscoroutinefunction(operation) else operation()
                results['disk_full'] = {
                    'status': 'success',
                    'duration': time.time() - start_time,
                    'disk_usage': self.disk_simulator.get_disk_info()['percent']
                }
            except Exception as e:
                results['disk_full'] = {'status': 'failure', 'error': str(e)}
        
        return results
    
    async def test_cpu_overload_handling(self, operation: Callable) -> Dict[str, Any]:
        """Test operation behavior under high CPU load"""
        results = {}
        
        # Test normal operation
        self.monitor.start_monitoring()
        try:
            start_time = time.time()
            await operation() if asyncio.iscoroutinefunction(operation) else operation()
            results['normal'] = {
                'status': 'success',
                'duration': time.time() - start_time,
                'peak_cpu': self.monitor.get_peak_usage()['cpu_percent']
            }
        except Exception as e:
            results['normal'] = {'status': 'failure', 'error': str(e)}
        finally:
            self.monitor.stop_monitoring()
        
        # Test under high CPU load
        with self.cpu_simulator.simulate_cpu_load(95.0, duration=30.0):
            self.monitor.start_monitoring()
            try:
                start_time = time.time()
                await operation() if asyncio.iscoroutinefunction(operation) else operation()
                results['cpu_overload'] = {
                    'status': 'success',
                    'duration': time.time() - start_time,
                    'peak_cpu': self.monitor.get_peak_usage()['cpu_percent']
                }
            except Exception as e:
                results['cpu_overload'] = {'status': 'failure', 'error': str(e)}
            finally:
                self.monitor.stop_monitoring()
        
        return results
    
    async def test_database_connection_exhaustion(self, operation: Callable) -> Dict[str, Any]:
        """Test operation behavior when database connections are exhausted"""
        results = {}
        
        # Test normal operation
        try:
            start_time = time.time()
            await operation() if asyncio.iscoroutinefunction(operation) else operation()
            results['normal'] = {
                'status': 'success',
                'duration': time.time() - start_time,
                'connections': self.db_simulator.get_connection_info()
            }
        except Exception as e:
            results['normal'] = {'status': 'failure', 'error': str(e)}
        
        # Test with connection exhaustion
        with self.db_simulator.simulate_connection_exhaustion():
            try:
                start_time = time.time()
                await operation() if asyncio.iscoroutinefunction(operation) else operation()
                results['connection_exhaustion'] = {
                    'status': 'success',
                    'duration': time.time() - start_time,
                    'connections': self.db_simulator.get_connection_info()
                }
            except Exception as e:
                results['connection_exhaustion'] = {'status': 'failure', 'error': str(e)}
        
        return results
    
    async def test_comprehensive_resource_exhaustion(self, operation: Callable) -> Dict[str, Any]:
        """Test operation under multiple resource constraints simultaneously"""
        results = {}
        
        # Test with multiple resource constraints
        with self.memory_simulator.simulate_memory_pressure(85.0), \
             self.cpu_simulator.simulate_cpu_load(90.0, duration=60.0), \
             self.db_simulator.simulate_connection_exhaustion():
            
            self.monitor.start_monitoring()
            try:
                start_time = time.time()
                await operation() if asyncio.iscoroutinefunction(operation) else operation()
                results['multiple_constraints'] = {
                    'status': 'success',
                    'duration': time.time() - start_time,
                    'peak_usage': self.monitor.get_peak_usage(),
                    'average_usage': self.monitor.get_average_usage()
                }
            except Exception as e:
                results['multiple_constraints'] = {
                    'status': 'failure',
                    'error': str(e),
                    'peak_usage': self.monitor.get_peak_usage(),
                    'average_usage': self.monitor.get_average_usage()
                }
            finally:
                self.monitor.stop_monitoring()
        
        return results