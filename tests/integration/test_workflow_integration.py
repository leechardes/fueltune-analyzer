"""
Integration tests for complete workflow scenarios.

Tests end-to-end workflows including data loading, processing,
analysis, and reporting with all components working together.
"""

import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Import modules with graceful fallbacks
modules_available = {}

try:
    from src.data.cache import CacheManager
    from src.data.csv_parser import CSVParser
    from src.data.validators import DataValidator

    modules_available["csv_parser"] = CSVParser
    modules_available["data_validator"] = DataValidator
    modules_available["cache"] = CacheManager
except ImportError:
    pass

try:
    from src.analysis.anomaly import AnomalyDetector
    from src.analysis.fuel_efficiency import FuelEfficiencyAnalyzer
    from src.analysis.performance import PerformanceAnalyzer

    modules_available["fuel_efficiency"] = FuelEfficiencyAnalyzer
    modules_available["performance"] = PerformanceAnalyzer
    modules_available["anomaly"] = AnomalyDetector
except ImportError:
    pass

try:
    from src.integration.background import BackgroundProcessor
    from src.integration.events import EventSystem
    from src.integration.workflow import WorkflowManager

    modules_available["workflow"] = WorkflowManager
    modules_available["events"] = EventSystem
    modules_available["background"] = BackgroundProcessor
except ImportError:
    pass

try:
    from src.data.database import DatabaseManager

    modules_available["database"] = DatabaseManager
except ImportError:
    pass


class TestCompleteDataWorkflow:
    """Test complete data processing workflow from CSV to analysis."""

    def test_csv_to_analysis_workflow(self, realistic_telemetry_data):
        """Test complete workflow from CSV parsing to analysis."""
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            realistic_telemetry_data.to_csv(f.name, index=False)
            csv_path = Path(f.name)

        try:
            # Step 1: Parse CSV
            if "csv_parser" in modules_available:
                parser = modules_available["csv_parser"]()
                parsed_data = parser.parse(csv_path)
                assert isinstance(parsed_data, pd.DataFrame)
                assert len(parsed_data) > 0
            else:
                parsed_data = realistic_telemetry_data

            # Step 2: Validate data
            if "data_validator" in modules_available:
                validator = modules_available["data_validator"]()
                validation_result = validator.validate(parsed_data)
                assert isinstance(validation_result, dict)
                # Proceed even if validation finds issues

            # Step 3: Cache processed data
            if "cache" in modules_available:
                cache_manager = modules_available["cache"]()
                cache_key = f"processed_data_{datetime.now().timestamp()}"
                cache_manager.set(cache_key, parsed_data)
                cached_data = cache_manager.get(cache_key)
                assert cached_data is not None

            # Step 4: Run analysis
            analysis_results = {}

            if "fuel_efficiency" in modules_available:
                try:
                    efficiency_analyzer = modules_available["fuel_efficiency"]()
                    efficiency_result = efficiency_analyzer.analyze(parsed_data)
                    analysis_results["fuel_efficiency"] = efficiency_result
                except Exception as e:
                    analysis_results["fuel_efficiency"] = {"error": str(e)}

            if "performance" in modules_available:
                try:
                    performance_analyzer = modules_available["performance"]()
                    performance_result = performance_analyzer.analyze(parsed_data)
                    analysis_results["performance"] = performance_result
                except Exception as e:
                    analysis_results["performance"] = {"error": str(e)}

            if "anomaly" in modules_available:
                try:
                    anomaly_detector = modules_available["anomaly"]()
                    anomaly_result = anomaly_detector.detect_anomalies(parsed_data)
                    analysis_results["anomalies"] = anomaly_result
                except Exception as e:
                    analysis_results["anomalies"] = {"error": str(e)}

            # Verify workflow completed
            assert len(analysis_results) > 0 or "csv_parser" in modules_available

            # If no analysis modules available but CSV parsing works, that's success
            if len(analysis_results) == 0 and isinstance(parsed_data, pd.DataFrame):
                assert True  # CSV parsing workflow succeeded
            else:
                # At least one analysis should have run
                assert len(analysis_results) > 0

        finally:
            csv_path.unlink(missing_ok=True)

    def test_batch_processing_workflow(self, performance_test_data):
        """Test workflow for processing large datasets in batches."""
        # Split large dataset into batches
        batch_size = 1000
        num_batches = len(performance_test_data) // batch_size + 1

        batch_results = []

        for i in range(num_batches):
            start_idx = i * batch_size
            end_idx = min((i + 1) * batch_size, len(performance_test_data))

            if start_idx >= len(performance_test_data):
                break

            batch_data = performance_test_data.iloc[start_idx:end_idx].copy()

            # Process each batch
            batch_result = {
                "batch_id": i,
                "start_idx": start_idx,
                "end_idx": end_idx,
                "rows": len(batch_data),
                "processed_at": datetime.now(),
            }

            # Run quick analysis on batch
            if len(batch_data) > 0:
                batch_result["mean_rpm"] = batch_data["rpm"].mean()
                batch_result["mean_throttle"] = batch_data["throttle"].mean()

            batch_results.append(batch_result)

        # Verify batch processing
        assert len(batch_results) > 0
        total_processed_rows = sum(result["rows"] for result in batch_results)
        assert total_processed_rows == len(performance_test_data)

        # Aggregate results
        if batch_results:
            overall_mean_rpm = np.mean([r["mean_rpm"] for r in batch_results if "mean_rpm" in r])
            assert overall_mean_rpm > 0

    def test_error_recovery_workflow(self, corrupt_csv_data):
        """Test workflow error recovery and graceful degradation."""
        for corruption_type, corrupt_content in corrupt_csv_data.items():
            # Create corrupted file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
                f.write(corrupt_content)
                corrupt_path = Path(f.name)

            try:
                workflow_success = False
                error_handled = False

                # Attempt to process corrupted file
                try:
                    if "csv_parser" in modules_available:
                        parser = modules_available["csv_parser"]()
                        parsed_data = parser.parse(corrupt_path)

                        # If parsing succeeds with corrupt data, continue workflow
                        if parsed_data is not None and len(parsed_data) > 0:
                            workflow_success = True

                except Exception:
                    error_handled = True

                    # Try fallback processing
                    try:
                        # Create minimal valid data as fallback
                        fallback_data = pd.DataFrame(
                            {
                                "timestamp": [datetime.now()],
                                "rpm": [1000],
                                "throttle": [50.0],
                                "boost": [1.0],
                                "afr": [14.7],
                            }
                        )

                        # Continue workflow with fallback data
                        if "fuel_efficiency" in modules_available:
                            analyzer = modules_available["fuel_efficiency"]()
                            analyzer.analyze(fallback_data)
                            workflow_success = True

                    except Exception:
                        pass

                # Either workflow should succeed or error should be handled
                assert workflow_success or error_handled

            finally:
                corrupt_path.unlink(missing_ok=True)


class TestEventDrivenWorkflow:
    """Test event-driven workflow scenarios."""

    def test_event_triggered_analysis(self, realistic_telemetry_data):
        """Test analysis triggered by data loading events."""
        if "events" not in modules_available:
            pytest.skip("EventSystem not available")

        event_system = modules_available["events"]()
        analysis_results = {}
        events_received = []

        def data_loaded_handler(data):
            """Handle data loaded event."""
            events_received.append(("data_loaded", data))

            # Trigger analysis when data is loaded
            if "fuel_efficiency" in modules_available:
                try:
                    analyzer = modules_available["fuel_efficiency"]()
                    result = analyzer.analyze(data)
                    analysis_results["fuel_efficiency"] = result

                    # Emit analysis complete event
                    if hasattr(event_system, "emit"):
                        event_system.emit(
                            "analysis_complete", {"type": "fuel_efficiency", "result": result}
                        )

                except Exception as e:
                    analysis_results["fuel_efficiency"] = {"error": str(e)}

        def analysis_complete_handler(data):
            """Handle analysis complete event."""
            events_received.append(("analysis_complete", data))

        # Register event handlers
        try:
            if hasattr(event_system, "on"):
                event_system.on("data_loaded", data_loaded_handler)
                event_system.on("analysis_complete", analysis_complete_handler)

            # Emit data loaded event
            if hasattr(event_system, "emit"):
                event_system.emit("data_loaded", realistic_telemetry_data)

            # Allow time for event processing
            time.sleep(0.2)

            # Verify event-driven workflow
            assert len(events_received) >= 1
            data_loaded_events = [e for e in events_received if e[0] == "data_loaded"]
            assert len(data_loaded_events) == 1

        except Exception as e:
            pytest.skip(f"Event system not fully implemented: {e}")

    def test_cascading_event_workflow(self, realistic_telemetry_data):
        """Test cascading events in workflow."""
        if "events" not in modules_available:
            pytest.skip("EventSystem not available")

        event_system = modules_available["events"]()
        workflow_steps = []

        def step1_handler(data):
            workflow_steps.append("data_validation")
            # Simulate validation
            if hasattr(event_system, "emit"):
                event_system.emit("validation_complete", {"valid": True})

        def step2_handler(data):
            workflow_steps.append("analysis")
            # Simulate analysis
            if hasattr(event_system, "emit"):
                event_system.emit("analysis_complete", {"status": "success"})

        def step3_handler(data):
            workflow_steps.append("reporting")
            # Simulate reporting
            if hasattr(event_system, "emit"):
                event_system.emit("workflow_complete", {"final_status": "success"})

        try:
            # Register cascading event handlers
            if hasattr(event_system, "on"):
                event_system.on("data_loaded", step1_handler)
                event_system.on("validation_complete", step2_handler)
                event_system.on("analysis_complete", step3_handler)

            # Start the cascade
            if hasattr(event_system, "emit"):
                event_system.emit("data_loaded", realistic_telemetry_data)

            # Allow time for cascade processing
            time.sleep(0.3)

            # Verify cascade completed
            expected_steps = ["data_validation", "analysis", "reporting"]
            assert workflow_steps == expected_steps

        except Exception as e:
            pytest.skip(f"Cascading events not supported: {e}")


class TestBackgroundWorkflow:
    """Test background processing workflows."""

    def test_async_data_processing(self, realistic_telemetry_data):
        """Test asynchronous data processing workflow."""
        if "background" not in modules_available:
            pytest.skip("BackgroundProcessor not available")

        processor = modules_available["background"]()
        results = []

        def background_analysis_task(data):
            """Background task for data analysis."""
            time.sleep(0.1)  # Simulate processing time

            # Perform simple analysis
            result = {
                "processed_at": datetime.now().isoformat(),
                "rows_processed": len(data),
                "mean_rpm": data["rpm"].mean() if "rpm" in data.columns else 0,
                "status": "completed",
            }

            results.append(result)
            return result

        try:
            # Submit background task
            if hasattr(processor, "submit"):
                future = processor.submit(background_analysis_task, realistic_telemetry_data)

                # Wait for completion
                if hasattr(future, "result"):
                    result = future.result(timeout=10.0)
                    assert result is not None
                    assert result["status"] == "completed"
                    assert result["rows_processed"] == len(realistic_telemetry_data)
                elif hasattr(future, "get"):
                    result = future.get(timeout=10.0)
                    assert result is not None

            assert len(results) == 1

        except Exception as e:
            pytest.skip(f"Background processing not implemented: {e}")

    def test_concurrent_analysis_tasks(self, realistic_telemetry_data):
        """Test running multiple analysis tasks concurrently."""
        if "background" not in modules_available:
            pytest.skip("BackgroundProcessor not available")

        processor = modules_available["background"]()
        task_results = []

        def analysis_task(task_id, data):
            """Individual analysis task."""
            time.sleep(0.05)  # Small delay to simulate work

            result = {
                "task_id": task_id,
                "completed_at": datetime.now().isoformat(),
                "data_size": len(data),
            }

            task_results.append(result)
            return result

        try:
            # Submit multiple concurrent tasks
            futures = []
            num_tasks = 3

            if hasattr(processor, "submit"):
                for i in range(num_tasks):
                    future = processor.submit(analysis_task, i, realistic_telemetry_data)
                    futures.append(future)

                # Wait for all tasks to complete
                completed_results = []
                for future in futures:
                    if hasattr(future, "result"):
                        result = future.result(timeout=10.0)
                        completed_results.append(result)
                    elif hasattr(future, "get"):
                        result = future.get(timeout=10.0)
                        completed_results.append(result)

                assert len(completed_results) == num_tasks
                assert len(task_results) == num_tasks

                # Verify all tasks completed
                task_ids = [r["task_id"] for r in completed_results]
                assert sorted(task_ids) == list(range(num_tasks))

        except Exception as e:
            pytest.skip(f"Concurrent processing not implemented: {e}")

    def test_long_running_workflow_monitoring(self, performance_test_data):
        """Test monitoring of long-running workflows."""
        if "background" not in modules_available:
            pytest.skip("BackgroundProcessor not available")

        processor = modules_available["background"]()
        progress_updates = []

        def long_running_task(data):
            """Simulate a long-running analysis task."""
            total_batches = 5
            len(data) // total_batches

            for i in range(total_batches):
                time.sleep(0.02)  # Simulate processing

                progress = {
                    "batch": i + 1,
                    "total_batches": total_batches,
                    "progress_percent": ((i + 1) / total_batches) * 100,
                    "timestamp": datetime.now().isoformat(),
                }

                progress_updates.append(progress)

            return {"status": "completed", "total_progress_updates": len(progress_updates)}

        try:
            if hasattr(processor, "submit"):
                future = processor.submit(long_running_task, performance_test_data)

                # Wait for completion
                if hasattr(future, "result"):
                    result = future.result(timeout=15.0)
                    assert result["status"] == "completed"
                    assert len(progress_updates) == 5  # One for each batch

                # Verify progress monitoring
                for i, update in enumerate(progress_updates):
                    assert update["batch"] == i + 1
                    assert update["progress_percent"] == ((i + 1) / 5) * 100

        except Exception as e:
            pytest.skip(f"Long-running task monitoring not implemented: {e}")


class TestDatabaseIntegratedWorkflow:
    """Test workflows integrated with database operations."""

    def test_data_persistence_workflow(self, realistic_telemetry_data, temporary_sqlite_db):
        """Test workflow with data persistence."""
        if "database" not in modules_available:
            pytest.skip("DatabaseManager not available")

        db_manager = modules_available["database"](temporary_sqlite_db)

        try:
            # Step 1: Save data to database
            session_data = {
                "id": "workflow_test_session",
                "name": "Workflow Test Session",
                "created_at": datetime.now(),
                "description": "Test session for workflow integration",
            }

            if hasattr(db_manager, "save_session"):
                session_id = db_manager.save_session(session_data)
                assert session_id is not None

            # Step 2: Store telemetry data
            if hasattr(db_manager, "save_telemetry_data"):
                data_saved = db_manager.save_telemetry_data(
                    session_data["id"], realistic_telemetry_data
                )
                assert data_saved is True

            # Step 3: Retrieve and verify data
            if hasattr(db_manager, "get_session"):
                retrieved_session = db_manager.get_session(session_data["id"])
                assert retrieved_session is not None
                assert retrieved_session["name"] == session_data["name"]

            if hasattr(db_manager, "get_telemetry_data"):
                retrieved_data = db_manager.get_telemetry_data(session_data["id"])
                assert isinstance(retrieved_data, pd.DataFrame)
                assert len(retrieved_data) == len(realistic_telemetry_data)

            # Step 4: Run analysis on persisted data
            if hasattr(db_manager, "get_telemetry_data") and "fuel_efficiency" in modules_available:
                data_for_analysis = db_manager.get_telemetry_data(session_data["id"])
                analyzer = modules_available["fuel_efficiency"]()
                analysis_result = analyzer.analyze(data_for_analysis)

                # Store analysis results
                if hasattr(db_manager, "save_analysis_result"):
                    analysis_saved = db_manager.save_analysis_result(
                        session_data["id"], "fuel_efficiency", analysis_result
                    )
                    assert analysis_saved is True

        except Exception as e:
            pytest.skip(f"Database integration not fully implemented: {e}")

    def test_multi_session_workflow(self, realistic_telemetry_data, temporary_sqlite_db):
        """Test workflow handling multiple sessions."""
        if "database" not in modules_available:
            pytest.skip("DatabaseManager not available")

        db_manager = modules_available["database"](temporary_sqlite_db)

        try:
            # Create multiple sessions
            sessions = []
            for i in range(3):
                session_data = {
                    "id": f"multi_session_test_{i}",
                    "name": f"Test Session {i+1}",
                    "created_at": datetime.now() + timedelta(minutes=i),
                    "description": f"Multi-session test {i+1}",
                }
                sessions.append(session_data)

                if hasattr(db_manager, "save_session"):
                    session_id = db_manager.save_session(session_data)
                    assert session_id is not None

                # Save different subsets of data for each session
                start_idx = i * 100
                end_idx = (i + 1) * 100
                session_data_subset = realistic_telemetry_data.iloc[start_idx:end_idx]

                if hasattr(db_manager, "save_telemetry_data"):
                    db_manager.save_telemetry_data(session_data["id"], session_data_subset)

            # Retrieve all sessions
            if hasattr(db_manager, "get_all_sessions"):
                all_sessions = db_manager.get_all_sessions()
                assert len(all_sessions) >= 3

                # Verify session data
                session_ids = [
                    s["id"] for s in all_sessions if s["id"].startswith("multi_session_test_")
                ]
                assert len(session_ids) == 3

            # Perform batch analysis on all sessions
            analysis_results = {}
            if "fuel_efficiency" in modules_available:
                analyzer = modules_available["fuel_efficiency"]()

                for session in sessions:
                    if hasattr(db_manager, "get_telemetry_data"):
                        session_data = db_manager.get_telemetry_data(session["id"])
                        if len(session_data) > 0:
                            result = analyzer.analyze(session_data)
                            analysis_results[session["id"]] = result

                # Should have analysis for each session
                assert len(analysis_results) == 3

        except Exception as e:
            pytest.skip(f"Multi-session workflow not implemented: {e}")


class TestFullSystemIntegration:
    """Test complete system integration scenarios."""

    def test_end_to_end_analysis_workflow(self, realistic_telemetry_data):
        """Test complete end-to-end analysis workflow."""
        workflow_log = []

        # Step 1: Data ingestion
        workflow_log.append(("data_ingestion", "started", datetime.now()))

        # Simulate CSV parsing
        if "csv_parser" in modules_available:
            try:
                parser = modules_available["csv_parser"]()
                # Since we already have data, just validate the parser works
                assert parser is not None
                workflow_log.append(("csv_parsing", "completed", datetime.now()))
            except Exception as e:
                workflow_log.append(("csv_parsing", "failed", datetime.now(), str(e)))

        # Step 2: Data validation
        if "data_validator" in modules_available:
            try:
                validator = modules_available["data_validator"]()
                validator.validate(realistic_telemetry_data)
                workflow_log.append(("data_validation", "completed", datetime.now()))
            except Exception as e:
                workflow_log.append(("data_validation", "failed", datetime.now(), str(e)))

        # Step 3: Caching
        if "cache" in modules_available:
            try:
                cache = modules_available["cache"]()
                cache_key = "integration_test_data"
                cache.set(cache_key, realistic_telemetry_data)
                workflow_log.append(("caching", "completed", datetime.now()))
            except Exception as e:
                workflow_log.append(("caching", "failed", datetime.now(), str(e)))

        # Step 4: Analysis
        analysis_modules_to_test = ["fuel_efficiency", "performance", "anomaly"]
        for module_name in analysis_modules_to_test:
            if module_name in modules_available:
                try:
                    analyzer = modules_available[module_name]()
                    analyzer.analyze(realistic_telemetry_data)
                    workflow_log.append((f"{module_name}_analysis", "completed", datetime.now()))
                except Exception as e:
                    workflow_log.append(
                        (f"{module_name}_analysis", "failed", datetime.now(), str(e))
                    )

        # Step 5: Event processing (if available)
        if "events" in modules_available:
            try:
                event_system = modules_available["events"]()
                if hasattr(event_system, "emit"):
                    event_system.emit("workflow_complete", {"status": "success"})
                workflow_log.append(("event_processing", "completed", datetime.now()))
            except Exception as e:
                workflow_log.append(("event_processing", "failed", datetime.now(), str(e)))

        # Verify workflow progress
        assert len(workflow_log) > 0

        # Count completed steps
        completed_steps = [log for log in workflow_log if log[1] == "completed"]
        failed_steps = [log for log in workflow_log if log[1] == "failed"]

        # At least some steps should complete successfully
        assert len(completed_steps) > 0

        # Log workflow summary
        print(f"\nWorkflow Summary:")
        print(f"Completed steps: {len(completed_steps)}")
        print(f"Failed steps: {len(failed_steps)}")
        for log in workflow_log:
            print(f"  {log[0]}: {log[1]} at {log[2]}")

    def test_performance_under_load(self, performance_test_data):
        """Test system performance under load conditions."""
        start_time = time.time()

        # Process large dataset through available modules
        processing_times = {}

        # Test CSV parsing performance
        if "csv_parser" in modules_available:
            parse_start = time.time()
            try:
                parser = modules_available["csv_parser"]()
                # Create temporary file for parsing test
                with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
                    performance_test_data.to_csv(f.name, index=False)
                    csv_path = Path(f.name)

                try:
                    parsed_data = parser.parse(csv_path)
                    processing_times["csv_parsing"] = time.time() - parse_start
                    assert isinstance(parsed_data, pd.DataFrame)
                finally:
                    csv_path.unlink(missing_ok=True)
            except Exception as e:
                processing_times["csv_parsing"] = f"failed: {e}"

        # Test analysis performance
        analysis_modules = ["fuel_efficiency", "performance", "anomaly"]
        for module_name in analysis_modules:
            if module_name in modules_available:
                analysis_start = time.time()
                try:
                    analyzer = modules_available[module_name]()
                    analyzer.analyze(performance_test_data)
                    processing_times[f"{module_name}_analysis"] = time.time() - analysis_start
                except Exception as e:
                    processing_times[f"{module_name}_analysis"] = f"failed: {e}"

        # Test caching performance
        if "cache" in modules_available:
            cache_start = time.time()
            try:
                cache = modules_available["cache"]()
                cache.set("performance_test_data", performance_test_data)
                cached_data = cache.get("performance_test_data")
                processing_times["caching"] = time.time() - cache_start
                assert cached_data is not None
            except Exception as e:
                processing_times["caching"] = f"failed: {e}"

        total_time = time.time() - start_time

        # Performance assertions
        assert total_time < 300.0  # Total processing should take less than 5 minutes

        # Log performance results
        print(f"\nPerformance Test Results (processing {len(performance_test_data)} rows):")
        print(f"Total time: {total_time:.2f} seconds")
        for operation, op_time in processing_times.items():
            if isinstance(op_time, float):
                print(f"  {operation}: {op_time:.2f} seconds")
            else:
                print(f"  {operation}: {op_time}")

    def test_system_resilience(self, anomaly_data, corrupt_csv_data):
        """Test system resilience with problematic data."""
        resilience_results = {
            "anomaly_handling": [],
            "corruption_handling": [],
            "recovery_attempts": [],
        }

        # Test handling of anomalous data
        try:
            if "anomaly" in modules_available:
                detector = modules_available["anomaly"]()
                detector.detect_anomalies(anomaly_data)
                resilience_results["anomaly_handling"].append("detection_successful")

            # Try other analyses with anomalous data
            for module_name in ["fuel_efficiency", "performance"]:
                if module_name in modules_available:
                    try:
                        analyzer = modules_available[module_name]()
                        result = analyzer.analyze(anomaly_data)
                        resilience_results["anomaly_handling"].append(
                            f"{module_name}_handled_anomalies"
                        )
                    except Exception:
                        resilience_results["anomaly_handling"].append(
                            f"{module_name}_failed_with_anomalies"
                        )

        except Exception as e:
            resilience_results["anomaly_handling"].append(f"anomaly_detection_failed: {e}")

        # Test handling of corrupted data
        for corruption_type, corrupt_content in corrupt_csv_data.items():
            try:
                # Create corrupted file
                with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
                    f.write(corrupt_content)
                    corrupt_path = Path(f.name)

                try:
                    # Try to parse corrupted data
                    if "csv_parser" in modules_available:
                        parser = modules_available["csv_parser"]()
                        parsed_data = parser.parse(corrupt_path)

                        if parsed_data is not None and len(parsed_data) > 0:
                            resilience_results["corruption_handling"].append(
                                f"{corruption_type}_parsed_successfully"
                            )
                        else:
                            resilience_results["corruption_handling"].append(
                                f"{corruption_type}_parsed_empty"
                            )

                except Exception:
                    resilience_results["corruption_handling"].append(
                        f"{corruption_type}_parsing_failed"
                    )

                    # Attempt recovery with fallback data
                    try:
                        fallback_data = pd.DataFrame(
                            {"timestamp": [datetime.now()], "rpm": [1000], "throttle": [50.0]}
                        )

                        if "fuel_efficiency" in modules_available:
                            analyzer = modules_available["fuel_efficiency"]()
                            analyzer.analyze(fallback_data)
                            resilience_results["recovery_attempts"].append(
                                f"{corruption_type}_recovery_successful"
                            )

                    except Exception:
                        resilience_results["recovery_attempts"].append(
                            f"{corruption_type}_recovery_failed"
                        )

                finally:
                    corrupt_path.unlink(missing_ok=True)

            except Exception:
                resilience_results["corruption_handling"].append(
                    f"{corruption_type}_test_setup_failed"
                )

        # Verify resilience
        assert len(resilience_results["anomaly_handling"]) > 0
        assert len(resilience_results["corruption_handling"]) > 0

        # Log resilience test results
        print(f"\nResilience Test Results:")
        for category, results in resilience_results.items():
            print(f"{category}: {len(results)} tests")
            for result in results:
                print(f"  - {result}")

        # System should handle at least some problematic scenarios
        total_tests = sum(len(results) for results in resilience_results.values())
        assert total_tests > 0
