"""
Performance Monitor Dashboard

This page provides comprehensive real-time performance monitoring
for the FuelTune Streamlit application.
"""

import sys
import time
from pathlib import Path

import streamlit as st

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

try:
    from src.performance.cache_integration import get_enhanced_cache_manager
    from src.performance.monitor import PerformanceMonitor
    from src.performance.optimizer import global_optimizer
    from src.performance.profiler import global_profiler
except ImportError as e:
    st.error(f"Error importing performance modules: {e}")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="Performance Monitor",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    """Main performance monitoring page."""

    st.title("Performance Monitor")
    st.markdown("Real-time system performance and optimization metrics")

    # Initialize performance monitor
    try:
        monitor = PerformanceMonitor()
    except Exception as e:
        st.error(f"Failed to initialize performance monitor: {e}")
        return

    # Sidebar controls
    with st.sidebar:
        st.header("Performance Controls")

        if st.button("Refresh Metrics", type="primary"):
            st.rerun()

        if st.button("Run Optimization"):
            with st.spinner("Running optimizations..."):
                # Memory cleanup
                cleanup_result = global_optimizer.memory_cleanup()

                # Cache optimization
                global_optimizer.optimize_streamlit_caching()

                st.success("Optimization completed!")
                st.info(f"Memory freed: {cleanup_result.memory_saved:.1f}MB")

        if st.button("Export Report"):
            try:
                report_path = Path("performance_report.json")
                global_profiler.export_results(report_path)
                st.success(f"Report exported to {report_path}")
            except Exception as e:
                st.error(f"Export failed: {e}")

        if st.button("Clear Cache"):
            try:
                cache_manager = get_enhanced_cache_manager()
                cache_manager.base_cache.clear_all()
                st.success("Cache cleared successfully")
            except Exception as e:
                st.error(f"Cache clear failed: {e}")

        # Monitoring controls
        st.header("Monitoring Settings")

        auto_refresh = st.checkbox("Auto Refresh (30s)", value=False)
        show_detailed = st.checkbox("Show Detailed Metrics", value=True)

        if auto_refresh:
            # Auto-refresh every 30 seconds
            time.sleep(30)
            st.rerun()

    # Main dashboard content
    try:
        # Render the performance dashboard
        monitor.render_dashboard()

        # Additional enhanced metrics if available
        if show_detailed:
            st.subheader("Enhanced Cache Analytics")

            try:
                cache_manager = get_enhanced_cache_manager()
                enhanced_metrics = cache_manager.get_enhanced_metrics()

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric(
                        "Enhanced Hit Rate",
                        f"{enhanced_metrics.hit_rate:.1%}",
                        help="Cache hit rate with enhanced tracking",
                    )

                with col2:
                    st.metric(
                        "Avg Access Time",
                        f"{enhanced_metrics.avg_access_time:.3f}s",
                        help="Average time to access cached data",
                    )

                with col3:
                    st.metric(
                        "Cache Efficiency",
                        f"{enhanced_metrics.cache_efficiency:.1f}%",
                        help="Overall cache performance efficiency",
                    )

                with col4:
                    st.metric(
                        "Total Requests",
                        f"{enhanced_metrics.total_requests:,}",
                        help="Total cache requests tracked",
                    )

                # Hot and cold keys analysis
                if enhanced_metrics.hot_keys or enhanced_metrics.cold_keys:
                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("**Hot Keys (Most Accessed):**")
                        if enhanced_metrics.hot_keys:
                            for i, key in enumerate(enhanced_metrics.hot_keys[:5], 1):
                                st.text(f"{i}. {key}")
                        else:
                            st.info("No hot keys data available")

                    with col2:
                        st.markdown("**Cold Keys (Least Accessed):**")
                        if enhanced_metrics.cold_keys:
                            for i, key in enumerate(enhanced_metrics.cold_keys[:5], 1):
                                st.text(f"{i}. {key}")
                        else:
                            st.info("No cold keys data available")

            except Exception as e:
                st.error(f"Error loading enhanced metrics: {e}")

        # Performance optimization recommendations
        st.subheader("Performance Recommendations")

        try:
            cache_manager = get_enhanced_cache_manager()
            optimization_analysis = cache_manager.optimize_cache_configuration()

            if "recommendations" in optimization_analysis:
                recommendations = optimization_analysis["recommendations"]

                if recommendations:
                    for recommendation in recommendations:
                        st.info(recommendation)
                else:
                    st.success(
                        "No performance recommendations at this time. System is running optimally."
                    )

        except Exception as e:
            st.warning(f"Unable to load optimization recommendations: {e}")

        # System information
        with st.expander("System Information"):
            try:
                import psutil

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**System Resources:**")
                    st.write(f"CPU Cores: {psutil.cpu_count()}")
                    st.write(f"Total Memory: {psutil.virtual_memory().total / 1024**3:.1f} GB")
                    st.write(
                        f"Available Memory: {psutil.virtual_memory().available / 1024**3:.1f} GB"
                    )

                with col2:
                    st.markdown("**Process Information:**")
                    process = psutil.Process()
                    st.write(f"Memory Usage: {process.memory_info().rss / 1024**2:.1f} MB")
                    st.write(f"CPU Percent: {process.cpu_percent():.1f}%")
                    st.write(f"Process ID: {process.pid}")

            except Exception as e:
                st.error(f"Unable to load system information: {e}")

    except Exception as e:
        st.error(f"Error rendering dashboard: {e}")
        st.markdown("**Debug Information:**")
        st.code(str(e))


if __name__ == "__main__":
    main()
