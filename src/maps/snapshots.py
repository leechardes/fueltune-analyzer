"""
Map Snapshots - Versioning system for tuning maps

This module provides comprehensive versioning and snapshot management
for tuning maps with SQLite storage, diff tracking, and rollback capabilities.

CRITICAL: Follows PYTHON-CODE-STANDARDS.md:
- Type hints 100% coverage
- Error handling comprehensive
- Professional database patterns
- Performance < 1s for operations
"""

import gzip
import hashlib
import json
import logging
import pickle
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class SnapshotMetadata:
    """Type-safe snapshot metadata container."""

    snapshot_id: str
    map_name: str
    map_type: str
    version: int
    parent_snapshot_id: Optional[str]
    created_at: datetime
    created_by: str
    description: Optional[str]
    tags: List[str]
    file_size: int
    data_hash: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result["created_at"] = self.created_at.isoformat()
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SnapshotMetadata":
        """Create from dictionary."""
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)


@dataclass
class SnapshotDiff:
    """Type-safe snapshot difference container."""

    cells_changed: int
    cells_added: int
    cells_removed: int
    mean_change: float
    max_change: float
    min_change: float
    change_summary: Dict[str, Any]


class MapSnapshots:
    """
    Professional versioning system for tuning maps.

    Features:
    - SQLite-based storage with compression
    - Diff tracking between versions
    - Rollback capabilities
    - Metadata tagging and search
    - Performance optimized for frequent snapshots
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize snapshot manager with database connection.

        Args:
            db_path: Optional path to SQLite database file
        """

        if db_path is None:
            db_path = Path("data/map_snapshots.db")

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_database()

        logger.debug(f"Initialized snapshot manager with database: {self.db_path}")

    def save_snapshot(
        self,
        map_data: pd.DataFrame,
        metadata: Any,  # MapMetadata type
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        created_by: str = "system",
    ) -> str:
        """
        Save map data as new snapshot with metadata.

        Args:
            map_data: Map DataFrame to save
            metadata: Map metadata object
            description: Optional description of changes
            tags: Optional tags for categorization
            created_by: User identifier

        Returns:
            Snapshot ID of saved snapshot

        Raises:
            ValueError: If map data is invalid
            DatabaseError: If save operation fails

        Performance: < 500ms for 32x32 maps
        """

        try:
            # Validate input
            if map_data.empty:
                raise ValueError("Cannot save empty map data")

            if tags is None:
                tags = []

            # Generate snapshot ID
            snapshot_id = self._generate_snapshot_id(map_data, metadata)

            # Check if identical snapshot already exists
            if self._snapshot_exists(snapshot_id):
                logger.warning(f"Identical snapshot {snapshot_id} already exists")
                return snapshot_id

            # Compress and serialize map data
            compressed_data = self._compress_map_data(map_data)
            data_hash = self._calculate_data_hash(compressed_data)

            # Find parent snapshot (latest version of same map)
            parent_id = self._find_latest_snapshot(metadata.name, metadata.map_type)

            # Calculate next version number
            next_version = self._get_next_version(metadata.name, metadata.map_type)

            # Create snapshot metadata
            snapshot_meta = SnapshotMetadata(
                snapshot_id=snapshot_id,
                map_name=metadata.name,
                map_type=metadata.map_type,
                version=next_version,
                parent_snapshot_id=parent_id,
                created_at=datetime.now(),
                created_by=created_by,
                description=description,
                tags=tags,
                file_size=len(compressed_data),
                data_hash=data_hash,
            )

            # Save to database
            with self._get_db_connection() as conn:
                cursor = conn.cursor()

                # Insert metadata
                cursor.execute(
                    """
                    INSERT INTO snapshots (
                        snapshot_id, map_name, map_type, version, 
                        parent_snapshot_id, created_at, created_by, 
                        description, tags, file_size, data_hash
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        snapshot_meta.snapshot_id,
                        snapshot_meta.map_name,
                        snapshot_meta.map_type,
                        snapshot_meta.version,
                        snapshot_meta.parent_snapshot_id,
                        snapshot_meta.created_at.isoformat(),
                        snapshot_meta.created_by,
                        snapshot_meta.description,
                        json.dumps(snapshot_meta.tags),
                        snapshot_meta.file_size,
                        snapshot_meta.data_hash,
                    ),
                )

                # Insert compressed data
                cursor.execute(
                    """
                    INSERT INTO snapshot_data (snapshot_id, compressed_data)
                    VALUES (?, ?)
                """,
                    (snapshot_id, compressed_data),
                )

                conn.commit()

            logger.info(f"Saved snapshot {snapshot_id} v{next_version} for {metadata.name}")

            return snapshot_id

        except Exception as e:
            logger.error(f"Failed to save snapshot: {e}")
            raise

    def load_snapshot(self, snapshot_id: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Load map data and metadata from snapshot.

        Args:
            snapshot_id: Snapshot identifier

        Returns:
            Tuple of (map_data, metadata_dict)

        Raises:
            ValueError: If snapshot not found

        Performance: < 200ms for typical snapshots
        """

        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()

                # Get snapshot metadata
                cursor.execute(
                    """
                    SELECT * FROM snapshots WHERE snapshot_id = ?
                """,
                    (snapshot_id,),
                )

                row = cursor.fetchone()
                if row is None:
                    raise ValueError(f"Snapshot {snapshot_id} not found")

                # Convert row to metadata
                columns = [desc[0] for desc in cursor.description]
                metadata_dict = dict(zip(columns, row))
                metadata_dict["created_at"] = datetime.fromisoformat(metadata_dict["created_at"])
                metadata_dict["tags"] = json.loads(metadata_dict["tags"])

                # Get compressed data
                cursor.execute(
                    """
                    SELECT compressed_data FROM snapshot_data WHERE snapshot_id = ?
                """,
                    (snapshot_id,),
                )

                data_row = cursor.fetchone()
                if data_row is None:
                    raise ValueError(f"Snapshot data {snapshot_id} not found")

                # Decompress map data
                map_data = self._decompress_map_data(data_row[0])

                logger.debug(f"Loaded snapshot {snapshot_id}")

                return map_data, metadata_dict

        except Exception as e:
            logger.error(f"Failed to load snapshot {snapshot_id}: {e}")
            raise

    def get_snapshot_history(
        self, map_name: Optional[str] = None, map_type: Optional[str] = None, limit: int = 50
    ) -> List[SnapshotMetadata]:
        """
        Get snapshot history with optional filtering.

        Args:
            map_name: Optional filter by map name
            map_type: Optional filter by map type
            limit: Maximum number of snapshots to return

        Returns:
            List of SnapshotMetadata objects

        Performance: < 100ms for typical queries
        """

        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()

                # Build query with filters
                query = "SELECT * FROM snapshots"
                params = []
                conditions = []

                if map_name is not None:
                    conditions.append("map_name = ?")
                    params.append(map_name)

                if map_type is not None:
                    conditions.append("map_type = ?")
                    params.append(map_type)

                if conditions:
                    query += " WHERE " + " AND ".join(conditions)

                query += " ORDER BY created_at DESC LIMIT ?"
                params.append(limit)

                cursor.execute(query, params)
                rows = cursor.fetchall()

                # Convert to metadata objects
                snapshots = []
                for row in rows:
                    columns = [desc[0] for desc in cursor.description]
                    data = dict(zip(columns, row))
                    data["created_at"] = datetime.fromisoformat(data["created_at"])
                    data["tags"] = json.loads(data["tags"])

                    snapshots.append(SnapshotMetadata(**data))

                logger.debug(f"Retrieved {len(snapshots)} snapshots from history")

                return snapshots

        except Exception as e:
            logger.error(f"Failed to get snapshot history: {e}")
            raise

    def compare_snapshots(self, snapshot_id_1: str, snapshot_id_2: str) -> SnapshotDiff:
        """
        Compare two snapshots and return differences.

        Args:
            snapshot_id_1: First snapshot ID (baseline)
            snapshot_id_2: Second snapshot ID (comparison)

        Returns:
            SnapshotDiff object with comparison results

        Performance: < 300ms for 32x32 map comparisons
        """

        try:
            # Load both snapshots
            map_1, meta_1 = self.load_snapshot(snapshot_id_1)
            map_2, meta_2 = self.load_snapshot(snapshot_id_2)

            # Ensure compatible dimensions
            if map_1.shape != map_2.shape:
                raise ValueError("Cannot compare snapshots with different dimensions")

            # Get numeric columns
            numeric_cols_1 = map_1.select_dtypes(include=[np.number]).columns
            numeric_cols_2 = map_2.select_dtypes(include=[np.number]).columns

            if not numeric_cols_1.equals(numeric_cols_2):
                raise ValueError("Cannot compare snapshots with different column structures")

            # Calculate differences
            diff_data = map_2[numeric_cols_2].values - map_1[numeric_cols_1].values

            # Compute statistics
            cells_changed = np.sum(np.abs(diff_data) > 1e-6)  # Account for floating point precision
            cells_added = 0  # For same-dimension maps
            cells_removed = 0  # For same-dimension maps

            non_zero_changes = diff_data[np.abs(diff_data) > 1e-6]
            if len(non_zero_changes) > 0:
                mean_change = np.mean(non_zero_changes)
                max_change = np.max(non_zero_changes)
                min_change = np.min(non_zero_changes)
            else:
                mean_change = max_change = min_change = 0.0

            # Create change summary
            change_summary = {
                "total_cells": diff_data.size,
                "unchanged_cells": diff_data.size - cells_changed,
                "percent_changed": (cells_changed / diff_data.size) * 100,
                "mean_absolute_change": np.mean(np.abs(diff_data)),
                "max_absolute_change": np.max(np.abs(diff_data)),
                "std_change": np.std(diff_data),
            }

            diff = SnapshotDiff(
                cells_changed=int(cells_changed),
                cells_added=cells_added,
                cells_removed=cells_removed,
                mean_change=float(mean_change),
                max_change=float(max_change),
                min_change=float(min_change),
                change_summary=change_summary,
            )

            logger.debug(
                f"Compared snapshots {snapshot_id_1} vs {snapshot_id_2}: "
                f"{cells_changed} cells changed"
            )

            return diff

        except Exception as e:
            logger.error(f"Failed to compare snapshots: {e}")
            raise

    def rollback_to_snapshot(self, snapshot_id: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Rollback to specific snapshot (loads the snapshot).

        Args:
            snapshot_id: Target snapshot ID

        Returns:
            Tuple of (map_data, metadata) from snapshot

        Note:
            This loads the snapshot data. The calling code is responsible
            for applying the rollback to the current map.
        """

        try:
            map_data, metadata = self.load_snapshot(snapshot_id)

            logger.info(f"Rollback prepared for snapshot {snapshot_id}")

            return map_data, metadata

        except Exception as e:
            logger.error(f"Rollback to snapshot {snapshot_id} failed: {e}")
            raise

    def delete_snapshot(self, snapshot_id: str) -> None:
        """
        Delete snapshot and its data.

        Args:
            snapshot_id: Snapshot ID to delete

        Raises:
            ValueError: If snapshot not found or has dependents
        """

        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()

                # Check if snapshot exists
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM snapshots WHERE snapshot_id = ?
                """,
                    (snapshot_id,),
                )

                if cursor.fetchone()[0] == 0:
                    raise ValueError(f"Snapshot {snapshot_id} not found")

                # Check if other snapshots depend on this one
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM snapshots WHERE parent_snapshot_id = ?
                """,
                    (snapshot_id,),
                )

                if cursor.fetchone()[0] > 0:
                    raise ValueError(
                        f"Cannot delete snapshot {snapshot_id}: other snapshots depend on it"
                    )

                # Delete snapshot data first
                cursor.execute(
                    """
                    DELETE FROM snapshot_data WHERE snapshot_id = ?
                """,
                    (snapshot_id,),
                )

                # Delete snapshot metadata
                cursor.execute(
                    """
                    DELETE FROM snapshots WHERE snapshot_id = ?
                """,
                    (snapshot_id,),
                )

                conn.commit()

            logger.info(f"Deleted snapshot {snapshot_id}")

        except Exception as e:
            logger.error(f"Failed to delete snapshot {snapshot_id}: {e}")
            raise

    def cleanup_old_snapshots(self, keep_count: int = 10, map_name: Optional[str] = None) -> int:
        """
        Clean up old snapshots, keeping only the most recent ones.

        Args:
            keep_count: Number of snapshots to keep per map
            map_name: Optional specific map to clean up

        Returns:
            Number of snapshots deleted

        Performance: < 1s for cleanup operations
        """

        try:
            deleted_count = 0

            with self._get_db_connection() as conn:
                cursor = conn.cursor()

                # Get distinct map combinations
                if map_name:
                    cursor.execute(
                        """
                        SELECT DISTINCT map_name, map_type FROM snapshots 
                        WHERE map_name = ?
                    """,
                        (map_name,),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT DISTINCT map_name, map_type FROM snapshots
                    """
                    )

                map_combinations = cursor.fetchall()

                # Process each map combination
                for map_name_val, map_type_val in map_combinations:
                    # Get snapshots for this map, ordered by creation date
                    cursor.execute(
                        """
                        SELECT snapshot_id FROM snapshots 
                        WHERE map_name = ? AND map_type = ?
                        ORDER BY created_at DESC
                    """,
                        (map_name_val, map_type_val),
                    )

                    snapshot_ids = [row[0] for row in cursor.fetchall()]

                    # Identify snapshots to delete (beyond keep_count)
                    if len(snapshot_ids) > keep_count:
                        to_delete = snapshot_ids[keep_count:]

                        for snapshot_id in to_delete:
                            try:
                                # Check for dependencies before deleting
                                cursor.execute(
                                    """
                                    SELECT COUNT(*) FROM snapshots WHERE parent_snapshot_id = ?
                                """,
                                    (snapshot_id,),
                                )

                                if cursor.fetchone()[0] == 0:
                                    # Safe to delete
                                    cursor.execute(
                                        """
                                        DELETE FROM snapshot_data WHERE snapshot_id = ?
                                    """,
                                        (snapshot_id,),
                                    )

                                    cursor.execute(
                                        """
                                        DELETE FROM snapshots WHERE snapshot_id = ?
                                    """,
                                        (snapshot_id,),
                                    )

                                    deleted_count += 1
                                    logger.debug(f"Deleted old snapshot {snapshot_id}")

                            except Exception as e:
                                logger.warning(f"Failed to delete snapshot {snapshot_id}: {e}")
                                continue

                conn.commit()

            logger.info(f"Cleanup completed: deleted {deleted_count} old snapshots")

            return deleted_count

        except Exception as e:
            logger.error(f"Snapshot cleanup failed: {e}")
            raise

    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics for snapshot database.

        Returns:
            Dictionary with storage information
        """

        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()

                # Count snapshots
                cursor.execute("SELECT COUNT(*) FROM snapshots")
                total_snapshots = cursor.fetchone()[0]

                # Calculate total storage size
                cursor.execute("SELECT SUM(file_size) FROM snapshots")
                total_size = cursor.fetchone()[0] or 0

                # Get database file size
                db_file_size = self.db_path.stat().st_size if self.db_path.exists() else 0

                # Count by map type
                cursor.execute(
                    """
                    SELECT map_type, COUNT(*) FROM snapshots GROUP BY map_type
                """
                )
                by_type = dict(cursor.fetchall())

                # Count by creation date (last 30 days)
                cursor.execute(
                    """
                    SELECT DATE(created_at), COUNT(*) FROM snapshots 
                    WHERE created_at >= datetime('now', '-30 days')
                    GROUP BY DATE(created_at)
                    ORDER BY DATE(created_at)
                """
                )
                recent_activity = dict(cursor.fetchall())

                return {
                    "total_snapshots": total_snapshots,
                    "total_compressed_size": total_size,
                    "database_file_size": db_file_size,
                    "compression_ratio": (
                        (db_file_size / max(total_size, 1)) if total_size > 0 else 0
                    ),
                    "snapshots_by_type": by_type,
                    "recent_activity": recent_activity,
                    "average_snapshot_size": total_size / max(total_snapshots, 1),
                }

        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            raise

    # Private helper methods

    def _init_database(self) -> None:
        """Initialize SQLite database with required tables."""

        with self._get_db_connection() as conn:
            cursor = conn.cursor()

            # Create snapshots metadata table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS snapshots (
                    snapshot_id TEXT PRIMARY KEY,
                    map_name TEXT NOT NULL,
                    map_type TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    parent_snapshot_id TEXT,
                    created_at TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    description TEXT,
                    tags TEXT,
                    file_size INTEGER NOT NULL,
                    data_hash TEXT NOT NULL,
                    FOREIGN KEY (parent_snapshot_id) REFERENCES snapshots (snapshot_id)
                )
            """
            )

            # Create snapshot data table (separate for performance)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS snapshot_data (
                    snapshot_id TEXT PRIMARY KEY,
                    compressed_data BLOB NOT NULL,
                    FOREIGN KEY (snapshot_id) REFERENCES snapshots (snapshot_id)
                )
            """
            )

            # Create indexes for performance
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_snapshots_map 
                ON snapshots (map_name, map_type)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_snapshots_created 
                ON snapshots (created_at)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_snapshots_version 
                ON snapshots (map_name, map_type, version)
            """
            )

            conn.commit()

    def _get_db_connection(self) -> sqlite3.Connection:
        """Get database connection with optimized settings."""

        conn = sqlite3.Connection(self.db_path)

        # Optimize SQLite settings
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA cache_size = 10000")

        return conn

    def _generate_snapshot_id(self, map_data: pd.DataFrame, metadata: Any) -> str:
        """Generate unique snapshot ID based on data and metadata."""

        # Create hash from data content and metadata
        data_str = str(map_data.values.tobytes())
        metadata_str = f"{metadata.name}_{metadata.map_type}_{datetime.now().isoformat()}"

        combined = data_str + metadata_str
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    def _snapshot_exists(self, snapshot_id: str) -> bool:
        """Check if snapshot already exists."""

        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM snapshots WHERE snapshot_id = ?", (snapshot_id,))
            return cursor.fetchone()[0] > 0

    def _compress_map_data(self, map_data: pd.DataFrame) -> bytes:
        """Compress map data for efficient storage."""

        # Serialize DataFrame to pickle
        pickled_data = pickle.dumps(map_data)

        # Compress with gzip
        compressed_data = gzip.compress(pickled_data, compresslevel=9)

        return compressed_data

    def _decompress_map_data(self, compressed_data: bytes) -> pd.DataFrame:
        """Decompress map data from storage."""

        # Decompress
        pickled_data = gzip.decompress(compressed_data)

        # Deserialize DataFrame
        map_data = pickle.loads(pickled_data)

        return map_data

    def _calculate_data_hash(self, data: bytes) -> str:
        """Calculate hash of data for integrity checking."""

        return hashlib.sha256(data).hexdigest()

    def _find_latest_snapshot(self, map_name: str, map_type: str) -> Optional[str]:
        """Find the latest snapshot ID for a given map."""

        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT snapshot_id FROM snapshots 
                WHERE map_name = ? AND map_type = ?
                ORDER BY version DESC, created_at DESC
                LIMIT 1
            """,
                (map_name, map_type),
            )

            row = cursor.fetchone()
            return row[0] if row else None

    def _get_next_version(self, map_name: str, map_type: str) -> int:
        """Get next version number for a map."""

        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT MAX(version) FROM snapshots 
                WHERE map_name = ? AND map_type = ?
            """,
                (map_name, map_type),
            )

            row = cursor.fetchone()
            max_version = row[0] if row and row[0] is not None else 0

            return max_version + 1
