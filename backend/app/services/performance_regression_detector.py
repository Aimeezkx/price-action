"""
Performance Regression Detection System

Advanced statistical analysis for detecting performance regressions
and anomalies in system metrics.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging
import statistics
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest

logger = logging.getLogger(__name__)


class RegressionType(Enum):
    """Types of performance regressions"""
    GRADUAL_DEGRADATION = "gradual_degradation"
    SUDDEN_SPIKE = "sudden_spike"
    ANOMALY = "anomaly"
    TREND_REVERSAL = "trend_reversal"


class ConfidenceLevel(Enum):
    """Confidence levels for regression detection"""
    LOW = 0.7
    MEDIUM = 0.8
    HIGH = 0.9
    VERY_HIGH = 0.95


@dataclass
class RegressionDetectionResult:
    """Result of regression detection analysis"""
    regression_detected: bool
    regression_type: Optional[RegressionType]
    confidence_score: float
    severity_score: float
    baseline_mean: float
    current_mean: float
    degradation_percentage: float
    statistical_significance: float
    detection_timestamp: datetime
    analysis_details: Dict[str, Any]
    recommendations: List[str]


@dataclass
class TimeSeriesAnalysis:
    """Time series analysis result"""
    trend: str  # increasing, decreasing, stable
    seasonality_detected: bool
    anomalies: List[Tuple[datetime, float]]
    change_points: List[datetime]
    forecast: List[float]
    confidence_intervals: List[Tuple[float, float]]


class PerformanceRegressionDetector:
    """Advanced performance regression detection"""
    
    def __init__(self):
        self.baseline_window_hours = 168  # 7 days
        self.comparison_window_hours = 24  # 1 day
        self.min_samples = 30
        self.anomaly_threshold = 2.0  # standard deviations
        
    async def detect_regression(self, 
                              metric_data: List[Dict[str, Any]],
                              metric_name: str) -> RegressionDetectionResult:
        """
        Detect performance regression using multiple statistical methods
        """
        if len(metric_data) < self.min_samples:
            return RegressionDetectionResult(
                regression_detected=False,
                regression_type=None,
                confidence_score=0.0,
                severity_score=0.0,
                baseline_mean=0.0,
                current_mean=0.0,
                degradation_percentage=0.0,
                statistical_significance=0.0,
                detection_timestamp=datetime.now(),
                analysis_details={"error": "Insufficient data"},
                recommendations=["Collect more data points for analysis"]
            )
            
        # Convert to pandas DataFrame for analysis
        df = pd.DataFrame(metric_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # Split into baseline and current periods
        cutoff_time = df['timestamp'].max() - timedelta(hours=self.comparison_window_hours)
        baseline_data = df[df['timestamp'] < cutoff_time]
        current_data = df[df['timestamp'] >= cutoff_time]
        
        if len(baseline_data) < 10 or len(current_data) < 10:
            return self._insufficient_data_result()
            
        # Perform multiple regression detection methods
        results = {}
        
        # 1. Statistical significance test
        results['statistical'] = await self._statistical_significance_test(
            baseline_data['value'].values, 
            current_data['value'].values
        )
        
        # 2. Change point detection
        results['change_point'] = await self._change_point_detection(df['value'].values)
        
        # 3. Anomaly detection
        results['anomaly'] = await self._anomaly_detection(df['value'].values)
        
        # 4. Trend analysis
        results['trend'] = await self._trend_analysis(df)
        
        # 5. Time series decomposition
        results['time_series'] = await self._time_series_analysis(df)
        
        # Combine results to make final determination
        return await self._combine_detection_results(
            results, baseline_data, current_data, metric_name
        )
        
    async def _statistical_significance_test(self, 
                                           baseline: np.ndarray, 
                                           current: np.ndarray) -> Dict[str, Any]:
        """Perform statistical significance tests"""
        try:
            # Welch's t-test (doesn't assume equal variances)
            t_stat, p_value = stats.ttest_ind(current, baseline, equal_var=False)
            
            # Mann-Whitney U test (non-parametric)
            u_stat, u_p_value = stats.mannwhitneyu(current, baseline, alternative='greater')
            
            # Effect size (Cohen's d)
            pooled_std = np.sqrt(((len(current) - 1) * np.var(current, ddof=1) + 
                                 (len(baseline) - 1) * np.var(baseline, ddof=1)) / 
                                (len(current) + len(baseline) - 2))
            cohens_d = (np.mean(current) - np.mean(baseline)) / pooled_std
            
            return {
                'significant_degradation': p_value < 0.05 and t_stat > 0,
                't_statistic': float(t_stat),
                'p_value': float(p_value),
                'u_p_value': float(u_p_value),
                'effect_size': float(cohens_d),
                'baseline_mean': float(np.mean(baseline)),
                'current_mean': float(np.mean(current)),
                'baseline_std': float(np.std(baseline)),
                'current_std': float(np.std(current))
            }
        except Exception as e:
            logger.error(f"Error in statistical significance test: {e}")
            return {'error': str(e)}
            
    async def _change_point_detection(self, values: np.ndarray) -> Dict[str, Any]:
        """Detect change points in the time series"""
        try:
            # Simple change point detection using cumulative sum
            cumsum = np.cumsum(values - np.mean(values))
            
            # Find points where cumulative sum changes direction significantly
            change_points = []
            window_size = max(10, len(values) // 10)
            
            for i in range(window_size, len(cumsum) - window_size):
                before_mean = np.mean(cumsum[i-window_size:i])
                after_mean = np.mean(cumsum[i:i+window_size])
                
                if abs(after_mean - before_mean) > 2 * np.std(cumsum):
                    change_points.append(i)
                    
            return {
                'change_points_detected': len(change_points) > 0,
                'change_point_indices': change_points,
                'cumulative_sum': cumsum.tolist()
            }
        except Exception as e:
            logger.error(f"Error in change point detection: {e}")
            return {'error': str(e)}
            
    async def _anomaly_detection(self, values: np.ndarray) -> Dict[str, Any]:
        """Detect anomalies using isolation forest"""
        try:
            # Reshape for sklearn
            X = values.reshape(-1, 1)
            
            # Use Isolation Forest for anomaly detection
            iso_forest = IsolationForest(contamination=0.1, random_state=42)
            anomaly_labels = iso_forest.fit_predict(X)
            
            # Also use statistical outlier detection
            z_scores = np.abs(stats.zscore(values))
            statistical_outliers = z_scores > self.anomaly_threshold
            
            anomaly_indices = np.where(anomaly_labels == -1)[0]
            statistical_outlier_indices = np.where(statistical_outliers)[0]
            
            return {
                'anomalies_detected': len(anomaly_indices) > 0,
                'anomaly_indices': anomaly_indices.tolist(),
                'statistical_outliers': statistical_outlier_indices.tolist(),
                'anomaly_scores': iso_forest.decision_function(X).tolist(),
                'z_scores': z_scores.tolist()
            }
        except Exception as e:
            logger.error(f"Error in anomaly detection: {e}")
            return {'error': str(e)}
            
    async def _trend_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze trends in the data"""
        try:
            values = df['value'].values
            time_indices = np.arange(len(values))
            
            # Linear regression for trend
            slope, intercept, r_value, p_value, std_err = stats.linregress(time_indices, values)
            
            # Determine trend direction
            if p_value < 0.05:  # Significant trend
                if slope > 0:
                    trend = "increasing"
                else:
                    trend = "decreasing"
            else:
                trend = "stable"
                
            # Calculate trend strength
            trend_strength = abs(r_value)
            
            return {
                'trend_direction': trend,
                'trend_strength': float(trend_strength),
                'slope': float(slope),
                'r_squared': float(r_value ** 2),
                'p_value': float(p_value),
                'significant_trend': p_value < 0.05
            }
        except Exception as e:
            logger.error(f"Error in trend analysis: {e}")
            return {'error': str(e)}
            
    async def _time_series_analysis(self, df: pd.DataFrame) -> TimeSeriesAnalysis:
        """Perform comprehensive time series analysis"""
        try:
            values = df['value'].values
            timestamps = df['timestamp'].values
            
            # Simple seasonality detection (look for periodic patterns)
            seasonality_detected = False
            if len(values) > 48:  # Need enough data
                # Check for daily patterns (assuming hourly data)
                daily_pattern = self._detect_seasonality(values, period=24)
                seasonality_detected = daily_pattern
                
            # Detect anomalies using moving average
            window_size = min(24, len(values) // 4)
            moving_avg = pd.Series(values).rolling(window=window_size).mean()
            moving_std = pd.Series(values).rolling(window=window_size).std()
            
            anomalies = []
            for i, (val, avg, std) in enumerate(zip(values, moving_avg, moving_std)):
                if not pd.isna(avg) and not pd.isna(std) and std > 0:
                    if abs(val - avg) > 2 * std:
                        anomalies.append((timestamps[i], val))
                        
            # Simple change point detection
            change_points = []
            if len(values) > 20:
                change_point_result = await self._change_point_detection(values)
                if not change_point_result.get('error'):
                    for idx in change_point_result.get('change_point_indices', []):
                        if idx < len(timestamps):
                            change_points.append(timestamps[idx])
                            
            return TimeSeriesAnalysis(
                trend="increasing" if np.polyfit(range(len(values)), values, 1)[0] > 0 else "decreasing",
                seasonality_detected=seasonality_detected,
                anomalies=anomalies,
                change_points=change_points,
                forecast=[],  # Would implement forecasting if needed
                confidence_intervals=[]
            )
        except Exception as e:
            logger.error(f"Error in time series analysis: {e}")
            return TimeSeriesAnalysis(
                trend="unknown",
                seasonality_detected=False,
                anomalies=[],
                change_points=[],
                forecast=[],
                confidence_intervals=[]
            )
            
    def _detect_seasonality(self, values: np.ndarray, period: int) -> bool:
        """Detect seasonality with given period"""
        try:
            if len(values) < 2 * period:
                return False
                
            # Autocorrelation at the specified lag
            correlation = np.corrcoef(values[:-period], values[period:])[0, 1]
            
            # Consider seasonal if correlation > 0.3
            return not np.isnan(correlation) and correlation > 0.3
        except:
            return False
            
    async def _combine_detection_results(self, 
                                       results: Dict[str, Any],
                                       baseline_data: pd.DataFrame,
                                       current_data: pd.DataFrame,
                                       metric_name: str) -> RegressionDetectionResult:
        """Combine all detection results into final determination"""
        
        baseline_mean = baseline_data['value'].mean()
        current_mean = current_data['value'].mean()
        degradation_percentage = ((current_mean - baseline_mean) / baseline_mean) * 100
        
        # Determine if regression is detected
        regression_detected = False
        regression_type = None
        confidence_score = 0.0
        severity_score = 0.0
        
        # Check statistical significance
        stat_result = results.get('statistical', {})
        if stat_result.get('significant_degradation', False):
            regression_detected = True
            confidence_score += 0.4
            
        # Check for anomalies
        anomaly_result = results.get('anomaly', {})
        if anomaly_result.get('anomalies_detected', False):
            regression_detected = True
            confidence_score += 0.2
            regression_type = RegressionType.ANOMALY
            
        # Check trend
        trend_result = results.get('trend', {})
        if (trend_result.get('trend_direction') == 'increasing' and 
            trend_result.get('significant_trend', False)):
            regression_detected = True
            confidence_score += 0.3
            if regression_type is None:
                regression_type = RegressionType.GRADUAL_DEGRADATION
                
        # Check change points
        change_point_result = results.get('change_point', {})
        if change_point_result.get('change_points_detected', False):
            confidence_score += 0.1
            if regression_type is None:
                regression_type = RegressionType.SUDDEN_SPIKE
                
        # Calculate severity based on degradation percentage
        if abs(degradation_percentage) > 50:
            severity_score = 1.0
        elif abs(degradation_percentage) > 25:
            severity_score = 0.7
        elif abs(degradation_percentage) > 10:
            severity_score = 0.4
        else:
            severity_score = 0.2
            
        # Generate recommendations
        recommendations = self._generate_recommendations(
            regression_detected, regression_type, degradation_percentage, results
        )
        
        return RegressionDetectionResult(
            regression_detected=regression_detected,
            regression_type=regression_type,
            confidence_score=min(confidence_score, 1.0),
            severity_score=severity_score,
            baseline_mean=float(baseline_mean),
            current_mean=float(current_mean),
            degradation_percentage=float(degradation_percentage),
            statistical_significance=float(stat_result.get('p_value', 1.0)),
            detection_timestamp=datetime.now(),
            analysis_details=results,
            recommendations=recommendations
        )
        
    def _generate_recommendations(self, 
                                regression_detected: bool,
                                regression_type: Optional[RegressionType],
                                degradation_percentage: float,
                                results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on detection results"""
        recommendations = []
        
        if not regression_detected:
            recommendations.append("No significant performance regression detected")
            recommendations.append("Continue monitoring for trends")
            return recommendations
            
        recommendations.append("Performance regression detected - immediate investigation recommended")
        
        if regression_type == RegressionType.SUDDEN_SPIKE:
            recommendations.extend([
                "Investigate recent deployments or configuration changes",
                "Check for resource exhaustion or external dependencies",
                "Review error logs for the time period of the spike"
            ])
        elif regression_type == RegressionType.GRADUAL_DEGRADATION:
            recommendations.extend([
                "Analyze long-term trends and resource usage patterns",
                "Consider capacity planning and scaling",
                "Review code changes over the degradation period"
            ])
        elif regression_type == RegressionType.ANOMALY:
            recommendations.extend([
                "Investigate anomalous data points",
                "Check for data quality issues",
                "Verify monitoring system accuracy"
            ])
            
        if abs(degradation_percentage) > 25:
            recommendations.append("High severity regression - consider immediate rollback if possible")
            
        # Add specific recommendations based on analysis results
        trend_result = results.get('trend', {})
        if trend_result.get('significant_trend'):
            recommendations.append("Significant trend detected - implement proactive monitoring")
            
        return recommendations
        
    def _insufficient_data_result(self) -> RegressionDetectionResult:
        """Return result for insufficient data"""
        return RegressionDetectionResult(
            regression_detected=False,
            regression_type=None,
            confidence_score=0.0,
            severity_score=0.0,
            baseline_mean=0.0,
            current_mean=0.0,
            degradation_percentage=0.0,
            statistical_significance=1.0,
            detection_timestamp=datetime.now(),
            analysis_details={"error": "Insufficient data for analysis"},
            recommendations=["Collect more data points for meaningful analysis"]
        )


# Global instance
regression_detector = PerformanceRegressionDetector()