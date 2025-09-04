"""
Performance Monitoring Dashboard for FuelTune Streamlit

This module provides a comprehensive real-time performance monitoring
dashboard with metrics visualization and alerting capabilities.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import time
import psutil
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import threading
from datetime import datetime, timedelta
import json
from pathlib import Path
import logging

from .profiler import ProfilerManager, global_profiler, SystemMetrics
from .optimizer import OptimizationEngine, global_optimizer

logger = logging.getLogger(__name__)


@dataclass
class PerformanceAlert:
    """Performance alert definition."""
    
    alert_type: str
    severity: str  # 'info', 'warning', 'error', 'critical'
    message: str
    threshold_value: float
    current_value: float
    timestamp: float
    resolved: bool = False


class PerformanceMonitor:
    """Comprehensive performance monitoring dashboard."""
    
    def __init__(self, profiler: Optional[ProfilerManager] = None, 
                 optimizer: Optional[OptimizationEngine] = None):
        """Initialize performance monitor.
        
        Args:
            profiler: Optional profiler instance
            optimizer: Optional optimizer instance
        """
        self.profiler = profiler or global_profiler
        self.optimizer = optimizer or global_optimizer
        self.alerts: List[PerformanceAlert] = []
        self._monitoring_active = False
        
        # Performance thresholds
        self.thresholds = {
            'cpu_warning': 75.0,
            'cpu_critical': 90.0,
            'memory_warning': 80.0,
            'memory_critical': 95.0,
            'response_time_warning': 2.0,  # seconds
            'response_time_critical': 5.0,
            'cache_hit_rate_warning': 0.5,  # 50%
            'cache_hit_rate_critical': 0.3   # 30%
        }
    
    def render_dashboard(self) -> None:
        """Render the complete performance monitoring dashboard."""
        st.title("Performance Monitoring Dashboard")
        st.markdown("Real-time system performance and optimization metrics")
        
        # Control buttons
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("Refresh Metrics"):
                st.rerun()
        
        with col2:
            if st.button("Run Optimization"):
                self._run_optimization()
                st.success("Optimization completed")
        
        with col3:
            if st.button("Clear Alerts"):
                self.alerts.clear()
                st.success("Alerts cleared")
        
        with col4:
            if st.button("Export Report"):
                self._export_performance_report()
                st.success("Report exported")
        
        # Performance overview
        self._render_performance_overview()
        
        # System metrics
        self._render_system_metrics()
        
        # Cache performance
        self._render_cache_performance()
        
        # Profiling results
        self._render_profiling_results()
        
        # Alerts and warnings
        self._render_alerts()
        
        # Optimization history
        self._render_optimization_history()
        
    def _render_performance_overview(self) -> None:
        """Render performance overview section."""
        st.subheader("System Overview")
        
        # Collect current metrics
        current_metrics = self.profiler.collect_system_metrics()
        cache_metrics = self.optimizer.intelligent_cache.get_metrics()
        
        # Create overview metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            cpu_color = self._get_status_color(current_metrics.cpu_percent, 
                                             self.thresholds['cpu_warning'],
                                             self.thresholds['cpu_critical'])
            st.metric(
                "CPU Usage",
                f"{current_metrics.cpu_percent:.1f}%",
                delta=None,
                help="Current CPU utilization"
            )
            
        with col2:
            memory_color = self._get_status_color(current_metrics.memory_percent,
                                                self.thresholds['memory_warning'],
                                                self.thresholds['memory_critical'])
            st.metric(
                "Memory Usage",
                f"{current_metrics.memory_percent:.1f}%",
                delta=f"{current_metrics.memory_available:.1f}GB available",
                help="Current memory utilization"
            )
            
        with col3:
            cache_color = self._get_status_color(cache_metrics.hit_rate,
                                               self.thresholds['cache_hit_rate_warning'],
                                               self.thresholds['cache_hit_rate_critical'],
                                               inverse=True)
            st.metric(
                "Cache Hit Rate",
                f"{cache_metrics.hit_rate:.1%}",
                delta=f"{cache_metrics.total_requests} requests",
                help="Cache effectiveness"
            )
            
        with col4:
            st.metric(
                "Active Processes",
                f"{current_metrics.process_count}",
                delta=None,
                help="Total system processes"
            )
        
        # Check for alerts
        self._check_performance_alerts(current_metrics, cache_metrics)
    
    def _render_system_metrics(self) -> None:
        """Render detailed system metrics charts."""
        st.subheader("System Metrics History")
        
        if len(self.profiler.system_metrics) < 2:
            st.info("Collecting system metrics... Please wait for data to accumulate.")
            return
        
        # Prepare data
        recent_metrics = self.profiler.system_metrics[-100:]  # Last 100 data points
        timestamps = [datetime.fromtimestamp(m.timestamp) for m in recent_metrics]
        cpu_values = [m.cpu_percent for m in recent_metrics]
        memory_values = [m.memory_percent for m in recent_metrics]
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=['CPU Usage', 'Memory Usage', 'Disk Usage', 'Network I/O'],
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": True}]]
        )
        
        # CPU Usage
        fig.add_trace(
            go.Scatter(
                x=timestamps,
                y=cpu_values,
                mode='lines',
                name='CPU %',
                line=dict(color='#1f77b4', width=2)
            ),
            row=1, col=1
        )
        
        # Memory Usage
        fig.add_trace(
            go.Scatter(
                x=timestamps,
                y=memory_values,
                mode='lines',
                name='Memory %',
                line=dict(color='#ff7f0e', width=2)
            ),
            row=1, col=2
        )
        
        # Disk Usage
        disk_values = [m.disk_usage for m in recent_metrics]
        fig.add_trace(
            go.Scatter(
                x=timestamps,
                y=disk_values,
                mode='lines',
                name='Disk %',
                line=dict(color='#2ca02c', width=2)
            ),
            row=2, col=1
        )
        
        # Network I/O
        bytes_sent = [m.network_io.get('bytes_sent', 0) / 1024 / 1024 for m in recent_metrics]  # MB
        bytes_recv = [m.network_io.get('bytes_recv', 0) / 1024 / 1024 for m in recent_metrics]  # MB
        
        fig.add_trace(
            go.Scatter(
                x=timestamps,
                y=bytes_sent,
                mode='lines',
                name='Sent (MB)',
                line=dict(color='#d62728', width=2)
            ),
            row=2, col=2
        )
        
        fig.add_trace(
            go.Scatter(
                x=timestamps,
                y=bytes_recv,
                mode='lines',
                name='Received (MB)',
                line=dict(color='#9467bd', width=2),
                yaxis="y2"
            ),
            row=2, col=2,
            secondary_y=True
        )
        
        # Update layout
        fig.update_layout(
            height=600,
            showlegend=True,
            title_text="System Performance Metrics Over Time"
        )
        
        # Add threshold lines
        fig.add_hline(
            y=self.thresholds['cpu_warning'],
            line_dash="dash",
            line_color="orange",
            annotation_text="CPU Warning",
            row=1, col=1
        )
        
        fig.add_hline(
            y=self.thresholds['memory_warning'],
            line_dash="dash",
            line_color="orange",
            annotation_text="Memory Warning",
            row=1, col=2
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_cache_performance(self) -> None:
        """Render cache performance metrics."""
        st.subheader("Cache Performance Analysis")
        
        cache_metrics = self.optimizer.intelligent_cache.get_metrics()
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Cache hit/miss pie chart
            fig_pie = go.Figure(data=[
                go.Pie(
                    labels=['Cache Hits', 'Cache Misses'],
                    values=[
                        cache_metrics.total_requests * cache_metrics.hit_rate,
                        cache_metrics.total_requests * cache_metrics.miss_rate
                    ],
                    hole=0.3,
                    marker_colors=['#2ca02c', '#d62728']
                )
            ])
            
            fig_pie.update_layout(
                title="Cache Hit/Miss Ratio",
                annotations=[dict(text=f'{cache_metrics.hit_rate:.1%}', x=0.5, y=0.5, font_size=20, showarrow=False)]
            )
            
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with col2:
            # Cache metrics summary
            st.markdown("**Cache Statistics:**")
            st.write(f"Total Requests: {cache_metrics.total_requests:,}")
            st.write(f"Hit Rate: {cache_metrics.hit_rate:.1%}")
            st.write(f"Miss Rate: {cache_metrics.miss_rate:.1%}")
            st.write(f"Cache Size: {cache_metrics.cache_size} items")
            st.write(f"Memory Usage: {cache_metrics.memory_usage:.1f} MB")
            st.write(f"Evictions: {cache_metrics.evictions}")
            
            # Performance recommendations
            st.markdown("**Recommendations:**")
            if cache_metrics.hit_rate < 0.7:
                st.warning("Consider increasing cache TTL or size")
            if cache_metrics.memory_usage > 500:
                st.warning("High cache memory usage detected")
            if cache_metrics.hit_rate > 0.9:
                st.success("Excellent cache performance!")
    
    def _render_profiling_results(self) -> None:
        """Render profiling results section."""
        st.subheader("Function Profiling Results")
        
        if not self.profiler.profile_results:
            st.info("No profiling data available. Run operations to collect profiling data.")
            return
        
        # Create profiling summary table
        profile_data = []
        for name, result in self.profiler.profile_results.items():
            profile_data.append({
                'Function': name,
                'Execution Time (s)': f"{result.execution_time:.3f}",
                'Memory Peak (MB)': f"{result.memory_peak:.1f}",
                'CPU %': f"{result.cpu_percent:.1f}",
                'Call Count': result.call_count,
                'Bottlenecks': len(result.bottlenecks)
            })
        
        if profile_data:
            df_profiles = pd.DataFrame(profile_data)
            st.dataframe(df_profiles, use_container_width=True)
            
            # Show detailed bottleneck analysis for selected function
            selected_function = st.selectbox(
                "Select function for detailed analysis:",
                options=list(self.profiler.profile_results.keys())
            )
            
            if selected_function:
                result = self.profiler.profile_results[selected_function]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Performance Bottlenecks:**")
                    if result.bottlenecks:
                        for bottleneck in result.bottlenecks:
                            st.warning(bottleneck)
                    else:
                        st.success("No significant bottlenecks detected")
                
                with col2:
                    st.markdown("**Top Function Calls:**")
                    for i, caller in enumerate(result.top_callers[:5], 1):
                        st.text(f"{i}. {caller}")
    
    def _render_alerts(self) -> None:
        """Render active alerts and warnings."""
        st.subheader("Performance Alerts")
        
        active_alerts = [alert for alert in self.alerts if not alert.resolved]
        
        if not active_alerts:
            st.success("No active performance alerts")
            return
        
        for alert in active_alerts:
            if alert.severity == 'critical':
                st.error(f"**{alert.alert_type}:** {alert.message}")
            elif alert.severity == 'warning':
                st.warning(f"**{alert.alert_type}:** {alert.message}")
            elif alert.severity == 'info':
                st.info(f"**{alert.alert_type}:** {alert.message}")
    
    def _render_optimization_history(self) -> None:
        """Render optimization history section."""
        st.subheader("Optimization History")
        
        if not self.optimizer.optimization_history:
            st.info("No optimization history available.")
            return
        
        # Create optimization summary
        opt_summary = self.optimizer.get_optimization_summary()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Optimizations", opt_summary['total_optimizations'])
        with col2:
            st.metric("Success Rate", f"{opt_summary['success_rate']:.1%}")
        with col3:
            st.metric("Memory Saved", f"{opt_summary['total_memory_saved']:.1f} MB")
        
        # Recent optimizations table
        recent_opts = self.optimizer.optimization_history[-10:]  # Last 10 optimizations
        opt_data = []
        
        for opt in recent_opts:
            opt_data.append({
                'Type': opt.optimization_type,
                'Success': '✓' if opt.success else '✗',
                'Performance Gain': f"{opt.performance_gain:.1f}%",
                'Memory Saved (MB)': f"{opt.memory_saved:.1f}",
                'Optimizations Applied': len(opt.applied_optimizations)
            })
        
        if opt_data:
            df_opts = pd.DataFrame(opt_data)
            st.dataframe(df_opts, use_container_width=True)
    
    def _check_performance_alerts(self, metrics: SystemMetrics, cache_metrics) -> None:
        """Check for performance issues and create alerts."""
        current_time = time.time()
        
        # CPU alerts
        if metrics.cpu_percent > self.thresholds['cpu_critical']:
            self.alerts.append(PerformanceAlert(
                alert_type="High CPU Usage",
                severity="critical",
                message=f"CPU usage is critically high at {metrics.cpu_percent:.1f}%",
                threshold_value=self.thresholds['cpu_critical'],
                current_value=metrics.cpu_percent,
                timestamp=current_time
            ))
        elif metrics.cpu_percent > self.thresholds['cpu_warning']:
            self.alerts.append(PerformanceAlert(
                alert_type="Elevated CPU Usage",
                severity="warning",
                message=f"CPU usage is elevated at {metrics.cpu_percent:.1f}%",
                threshold_value=self.thresholds['cpu_warning'],
                current_value=metrics.cpu_percent,
                timestamp=current_time
            ))
        
        # Memory alerts
        if metrics.memory_percent > self.thresholds['memory_critical']:
            self.alerts.append(PerformanceAlert(
                alert_type="High Memory Usage",
                severity="critical",
                message=f"Memory usage is critically high at {metrics.memory_percent:.1f}%",
                threshold_value=self.thresholds['memory_critical'],
                current_value=metrics.memory_percent,
                timestamp=current_time
            ))
        elif metrics.memory_percent > self.thresholds['memory_warning']:
            self.alerts.append(PerformanceAlert(
                alert_type="Elevated Memory Usage",
                severity="warning",
                message=f"Memory usage is elevated at {metrics.memory_percent:.1f}%",
                threshold_value=self.thresholds['memory_warning'],
                current_value=metrics.memory_percent,
                timestamp=current_time
            ))
        
        # Cache alerts
        if cache_metrics.hit_rate < self.thresholds['cache_hit_rate_critical']:
            self.alerts.append(PerformanceAlert(
                alert_type="Poor Cache Performance",
                severity="critical",
                message=f"Cache hit rate is critically low at {cache_metrics.hit_rate:.1%}",
                threshold_value=self.thresholds['cache_hit_rate_critical'],
                current_value=cache_metrics.hit_rate,
                timestamp=current_time
            ))
        elif cache_metrics.hit_rate < self.thresholds['cache_hit_rate_warning']:
            self.alerts.append(PerformanceAlert(
                alert_type="Suboptimal Cache Performance",
                severity="warning",
                message=f"Cache hit rate is below optimal at {cache_metrics.hit_rate:.1%}",
                threshold_value=self.thresholds['cache_hit_rate_warning'],
                current_value=cache_metrics.hit_rate,
                timestamp=current_time
            ))
        
        # Keep only recent alerts (last 24 hours)
        cutoff_time = current_time - (24 * 3600)
        self.alerts = [alert for alert in self.alerts if alert.timestamp > cutoff_time]
    
    def _get_status_color(self, value: float, warning_threshold: float, 
                         critical_threshold: float, inverse: bool = False) -> str:
        """Get status color based on thresholds.
        
        Args:
            value: Current value
            warning_threshold: Warning threshold
            critical_threshold: Critical threshold
            inverse: If True, lower values are worse
            
        Returns:
            Color string
        """
        if inverse:
            if value < critical_threshold:
                return "red"
            elif value < warning_threshold:
                return "orange"
            else:
                return "green"
        else:
            if value > critical_threshold:
                return "red"
            elif value > warning_threshold:
                return "orange"
            else:
                return "green"
    
    def _run_optimization(self) -> None:
        """Run comprehensive optimization."""
        # Memory cleanup
        self.optimizer.memory_cleanup()
        
        # Cache optimization
        self.optimizer.optimize_streamlit_caching()
        
        # Start continuous monitoring if not active
        if not self.optimizer._memory_monitor_active:
            self.optimizer.start_continuous_monitoring()
    
    def _export_performance_report(self) -> None:
        """Export comprehensive performance report."""
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'system_metrics': [],
            'cache_metrics': self.optimizer.intelligent_cache.get_metrics().__dict__,
            'profiling_results': {},
            'optimization_summary': self.optimizer.get_optimization_summary(),
            'active_alerts': [
                {
                    'alert_type': alert.alert_type,
                    'severity': alert.severity,
                    'message': alert.message,
                    'timestamp': alert.timestamp
                }
                for alert in self.alerts if not alert.resolved
            ]
        }
        
        # Add recent system metrics
        for metric in self.profiler.system_metrics[-100:]:
            report_data['system_metrics'].append({
                'timestamp': metric.timestamp,
                'cpu_percent': metric.cpu_percent,
                'memory_percent': metric.memory_percent,
                'memory_available': metric.memory_available,
                'disk_usage': metric.disk_usage,
                'network_io': metric.network_io,
                'process_count': metric.process_count
            })
        
        # Add profiling results
        for name, result in self.profiler.profile_results.items():
            report_data['profiling_results'][name] = {
                'execution_time': result.execution_time,
                'memory_peak': result.memory_peak,
                'cpu_percent': result.cpu_percent,
                'call_count': result.call_count,
                'bottlenecks': result.bottlenecks
            }
        
        # Save report
        report_path = Path("performance_report.json")
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"Performance report exported to: {report_path}")


# Global monitor instance
global_monitor = PerformanceMonitor()