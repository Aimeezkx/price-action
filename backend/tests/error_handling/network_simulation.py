"""
Network Failure Simulation Utilities

This module provides utilities for simulating various network failure conditions
to test error handling and recovery mechanisms.

Requirements covered: 6.2 - Network failure handling
"""

import asyncio
import time
import random
from contextlib import contextmanager
from unittest.mock import patch, MagicMock
from typing import Dict, Any, Callable, Optional
import requests
from requests.exceptions import ConnectionError, Timeout, HTTPError


class NetworkSimulator:
    """Simulate various network failure conditions"""
    
    def __init__(self):
        self.failure_count = 0
        self.total_requests = 0
        self.failure_rate = 0.0
        
    @contextmanager
    def simulate_complete_network_loss(self, duration: float = 5.0):
        """Simulate complete network disconnection"""
        def network_failure(*args, **kwargs):
            raise ConnectionError("Network is unreachable")
        
        with patch('requests.get', side_effect=network_failure), \
             patch('requests.post', side_effect=network_failure), \
             patch('requests.put', side_effect=network_failure), \
             patch('requests.delete', side_effect=network_failure):
            yield
    
    @contextmanager
    def simulate_intermittent_connection(self, failure_rate: float = 0.3):
        """Simulate intermittent network failures"""
        self.failure_rate = failure_rate
        self.failure_count = 0
        self.total_requests = 0
        
        def intermittent_failure(*args, **kwargs):
            self.total_requests += 1
            if random.random() < self.failure_rate:
                self.failure_count += 1
                raise ConnectionError("Intermittent network failure")
            
            # Simulate successful response
            response = MagicMock()
            response.status_code = 200
            response.json.return_value = {'status': 'success'}
            return response
        
        with patch('requests.get', side_effect=intermittent_failure), \
             patch('requests.post', side_effect=intermittent_failure):
            yield
    
    @contextmanager
    def simulate_slow_connection(self, delay: float = 2.0, timeout: float = 1.0):
        """Simulate slow network connection with timeouts"""
        def slow_response(*args, **kwargs):
            # Check if timeout is specified in kwargs
            request_timeout = kwargs.get('timeout', timeout)
            
            if delay > request_timeout:
                raise Timeout("Request timed out")
            
            # Simulate slow response
            time.sleep(min(delay, request_timeout))
            
            response = MagicMock()
            response.status_code = 200
            response.json.return_value = {'status': 'success', 'delay': delay}
            return response
        
        with patch('requests.get', side_effect=slow_response), \
             patch('requests.post', side_effect=slow_response):
            yield
    
    @contextmanager
    def simulate_service_unavailable(self, error_code: int = 503):
        """Simulate service unavailable errors"""
        def service_error(*args, **kwargs):
            response = MagicMock()
            response.status_code = error_code
            response.raise_for_status.side_effect = HTTPError(f"HTTP {error_code} Error")
            return response
        
        with patch('requests.get', side_effect=service_error), \
             patch('requests.post', side_effect=service_error):
            yield
    
    @contextmanager
    def simulate_dns_failure(self):
        """Simulate DNS resolution failures"""
        def dns_failure(*args, **kwargs):
            raise ConnectionError("Name resolution failed")
        
        with patch('requests.get', side_effect=dns_failure), \
             patch('requests.post', side_effect=dns_failure):
            yield
    
    @contextmanager
    def simulate_bandwidth_throttling(self, bandwidth_limit: int = 1024):
        """Simulate bandwidth throttling (bytes per second)"""
        def throttled_response(*args, **kwargs):
            # Simulate data transfer with bandwidth limit
            data_size = 1024  # Assume 1KB response
            transfer_time = data_size / bandwidth_limit
            
            time.sleep(transfer_time)
            
            response = MagicMock()
            response.status_code = 200
            response.json.return_value = {'status': 'success', 'bandwidth': bandwidth_limit}
            return response
        
        with patch('requests.get', side_effect=throttled_response), \
             patch('requests.post', side_effect=throttled_response):
            yield
    
    def get_failure_statistics(self) -> Dict[str, Any]:
        """Get statistics about simulated failures"""
        return {
            'total_requests': self.total_requests,
            'failed_requests': self.failure_count,
            'failure_rate': self.failure_count / self.total_requests if self.total_requests > 0 else 0,
            'success_rate': 1 - (self.failure_count / self.total_requests) if self.total_requests > 0 else 1
        }


class RetryMechanism:
    """Test retry mechanisms with different strategies"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.attempt_count = 0
        
    async def exponential_backoff_retry(self, operation: Callable, *args, **kwargs) -> Any:
        """Retry operation with exponential backoff"""
        self.attempt_count = 0
        
        for attempt in range(self.max_retries + 1):
            self.attempt_count += 1
            
            try:
                result = await operation(*args, **kwargs) if asyncio.iscoroutinefunction(operation) else operation(*args, **kwargs)
                return result
            except Exception as e:
                if attempt == self.max_retries:
                    raise e
                
                # Exponential backoff delay
                delay = self.base_delay * (2 ** attempt)
                await asyncio.sleep(delay)
        
        raise Exception("Max retries exceeded")
    
    async def linear_backoff_retry(self, operation: Callable, *args, **kwargs) -> Any:
        """Retry operation with linear backoff"""
        self.attempt_count = 0
        
        for attempt in range(self.max_retries + 1):
            self.attempt_count += 1
            
            try:
                result = await operation(*args, **kwargs) if asyncio.iscoroutinefunction(operation) else operation(*args, **kwargs)
                return result
            except Exception as e:
                if attempt == self.max_retries:
                    raise e
                
                # Linear backoff delay
                delay = self.base_delay * (attempt + 1)
                await asyncio.sleep(delay)
        
        raise Exception("Max retries exceeded")
    
    async def immediate_retry(self, operation: Callable, *args, **kwargs) -> Any:
        """Retry operation immediately without delay"""
        self.attempt_count = 0
        
        for attempt in range(self.max_retries + 1):
            self.attempt_count += 1
            
            try:
                result = await operation(*args, **kwargs) if asyncio.iscoroutinefunction(operation) else operation(*args, **kwargs)
                return result
            except Exception as e:
                if attempt == self.max_retries:
                    raise e
        
        raise Exception("Max retries exceeded")
    
    def get_retry_statistics(self) -> Dict[str, Any]:
        """Get statistics about retry attempts"""
        return {
            'total_attempts': self.attempt_count,
            'max_retries': self.max_retries,
            'base_delay': self.base_delay
        }


class CircuitBreaker:
    """Circuit breaker pattern for handling repeated failures"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
        
    async def call(self, operation: Callable, *args, **kwargs) -> Any:
        """Execute operation through circuit breaker"""
        if self.state == 'OPEN':
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = 'HALF_OPEN'
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await operation(*args, **kwargs) if asyncio.iscoroutinefunction(operation) else operation(*args, **kwargs)
            
            # Success - reset failure count and close circuit
            if self.state == 'HALF_OPEN':
                self.state = 'CLOSED'
                self.failure_count = 0
            
            return result
            
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = 'OPEN'
            
            raise e
    
    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state"""
        return {
            'state': self.state,
            'failure_count': self.failure_count,
            'failure_threshold': self.failure_threshold,
            'last_failure_time': self.last_failure_time,
            'recovery_timeout': self.recovery_timeout
        }
    
    def reset(self):
        """Reset circuit breaker to initial state"""
        self.state = 'CLOSED'
        self.failure_count = 0
        self.last_failure_time = 0


class OfflineMode:
    """Simulate offline mode functionality"""
    
    def __init__(self):
        self.is_offline = False
        self.cached_data = {}
        self.pending_operations = []
        
    def activate_offline_mode(self):
        """Activate offline mode"""
        self.is_offline = True
        
    def deactivate_offline_mode(self):
        """Deactivate offline mode and sync pending operations"""
        self.is_offline = False
        return self.sync_pending_operations()
    
    def cache_data(self, key: str, data: Any):
        """Cache data for offline access"""
        self.cached_data[key] = data
    
    def get_cached_data(self, key: str) -> Optional[Any]:
        """Retrieve cached data"""
        return self.cached_data.get(key)
    
    def queue_operation(self, operation: Dict[str, Any]):
        """Queue operation for later execution when online"""
        if self.is_offline:
            self.pending_operations.append(operation)
            return True
        return False
    
    async def sync_pending_operations(self) -> Dict[str, Any]:
        """Sync pending operations when back online"""
        if self.is_offline:
            return {'status': 'error', 'message': 'Still offline'}
        
        synced_operations = []
        failed_operations = []
        
        for operation in self.pending_operations:
            try:
                # Simulate operation execution
                await asyncio.sleep(0.1)  # Simulate network delay
                synced_operations.append(operation)
            except Exception as e:
                failed_operations.append({'operation': operation, 'error': str(e)})
        
        # Clear successfully synced operations
        self.pending_operations = [op for op in self.pending_operations 
                                 if op not in synced_operations]
        
        return {
            'status': 'success',
            'synced_operations': len(synced_operations),
            'failed_operations': len(failed_operations),
            'remaining_operations': len(self.pending_operations)
        }
    
    def get_offline_status(self) -> Dict[str, Any]:
        """Get current offline mode status"""
        return {
            'is_offline': self.is_offline,
            'cached_items': len(self.cached_data),
            'pending_operations': len(self.pending_operations)
        }


# Test utilities for network failure scenarios

async def test_network_resilience(operation: Callable, simulator: NetworkSimulator) -> Dict[str, Any]:
    """Test operation resilience under various network conditions"""
    test_results = {}
    
    # Test complete network loss
    with simulator.simulate_complete_network_loss():
        try:
            await operation() if asyncio.iscoroutinefunction(operation) else operation()
            test_results['network_loss'] = {'status': 'unexpected_success'}
        except Exception as e:
            test_results['network_loss'] = {'status': 'expected_failure', 'error': str(e)}
    
    # Test intermittent connection
    with simulator.simulate_intermittent_connection(failure_rate=0.5):
        try:
            await operation() if asyncio.iscoroutinefunction(operation) else operation()
            test_results['intermittent'] = {'status': 'success_with_retries'}
        except Exception as e:
            test_results['intermittent'] = {'status': 'failure', 'error': str(e)}
    
    # Test slow connection
    with simulator.simulate_slow_connection(delay=2.0, timeout=1.0):
        try:
            await operation() if asyncio.iscoroutinefunction(operation) else operation()
            test_results['slow_connection'] = {'status': 'unexpected_success'}
        except Exception as e:
            test_results['slow_connection'] = {'status': 'expected_timeout', 'error': str(e)}
    
    return test_results


async def test_retry_strategies(operation: Callable) -> Dict[str, Any]:
    """Test different retry strategies"""
    results = {}
    
    # Test exponential backoff
    retry_mechanism = RetryMechanism(max_retries=3, base_delay=0.1)
    try:
        start_time = time.time()
        await retry_mechanism.exponential_backoff_retry(operation)
        results['exponential_backoff'] = {
            'status': 'success',
            'duration': time.time() - start_time,
            'attempts': retry_mechanism.attempt_count
        }
    except Exception as e:
        results['exponential_backoff'] = {
            'status': 'failure',
            'error': str(e),
            'attempts': retry_mechanism.attempt_count
        }
    
    # Test linear backoff
    retry_mechanism = RetryMechanism(max_retries=3, base_delay=0.1)
    try:
        start_time = time.time()
        await retry_mechanism.linear_backoff_retry(operation)
        results['linear_backoff'] = {
            'status': 'success',
            'duration': time.time() - start_time,
            'attempts': retry_mechanism.attempt_count
        }
    except Exception as e:
        results['linear_backoff'] = {
            'status': 'failure',
            'error': str(e),
            'attempts': retry_mechanism.attempt_count
        }
    
    return results


async def test_circuit_breaker_behavior(operation: Callable) -> Dict[str, Any]:
    """Test circuit breaker behavior under failures"""
    circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=1.0)
    results = []
    
    # Trigger failures to open circuit
    for i in range(5):
        try:
            await circuit_breaker.call(operation)
            results.append({'attempt': i + 1, 'status': 'success', 'circuit_state': circuit_breaker.state})
        except Exception as e:
            results.append({'attempt': i + 1, 'status': 'failure', 'error': str(e), 'circuit_state': circuit_breaker.state})
    
    # Wait for recovery timeout
    await asyncio.sleep(1.1)
    
    # Test recovery
    try:
        await circuit_breaker.call(operation)
        results.append({'attempt': 'recovery', 'status': 'success', 'circuit_state': circuit_breaker.state})
    except Exception as e:
        results.append({'attempt': 'recovery', 'status': 'failure', 'error': str(e), 'circuit_state': circuit_breaker.state})
    
    return {
        'results': results,
        'final_state': circuit_breaker.get_state()
    }