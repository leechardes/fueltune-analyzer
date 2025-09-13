"""Unify FuelTech core and extended data into a single table

Revision ID: unify_core_extended_001
Revises: fuel_maps_001
Create Date: 2025-09-10 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'unify_core_extended_001'
# Place this after fuel_banks_001 to ensure vehicles schema exists; it does not depend on fuel_maps tables
down_revision = 'fuel_banks_001'
branch_labels = None
depends_on = None


def upgrade():
    """Add extended columns to fueltech_core_data, migrate data, drop extended table."""
    # 1) Add columns from fueltech_extended_data into fueltech_core_data
    cols = [
        ("total_consumption", sa.Float()),
        ("average_consumption", sa.Float()),
        ("instant_consumption", sa.Float()),
        ("total_distance", sa.Float()),
        ("range", sa.Float()),
        ("estimated_power", sa.Integer()),
        ("estimated_torque", sa.Integer()),
        ("traction_speed", sa.Float()),
        ("acceleration_speed", sa.Float()),
        ("acceleration_distance", sa.Float()),
        ("traction_control_slip", sa.Float()),
        ("traction_control_slip_rate", sa.Integer()),
        ("delta_tps", sa.Float()),
        ("g_force_accel", sa.Float()),
        ("g_force_lateral", sa.Float()),
        ("g_force_accel_raw", sa.Float()),
        ("g_force_lateral_raw", sa.Float()),
        ("pitch_angle", sa.Float()),
        ("pitch_rate", sa.Float()),
        ("roll_angle", sa.Float()),
        ("roll_rate", sa.Float()),
        ("heading", sa.Float()),
        ("accel_enrichment", sa.String(10)),
        ("decel_enrichment", sa.String(10)),
        ("injection_cutoff", sa.String(10)),
        ("after_start_injection", sa.String(10)),
        ("start_button_toggle", sa.String(10)),
    ]

    for name, coltype in cols:
        op.add_column('fueltech_core_data', sa.Column(name, coltype))

    # 2) Migrate data from fueltech_extended_data to fueltech_core_data by (session_id, time)
    # Note: SQLite does not support UPDATE ... FROM; use correlated subqueries per column
    conn = op.get_bind()
    for name, _ in cols:
        conn.execute(
            sa.text(
                f"""
                UPDATE fueltech_core_data
                SET {name} = (
                    SELECT e.{name}
                    FROM fueltech_extended_data e
                    WHERE e.session_id = fueltech_core_data.session_id
                      AND e.time = fueltech_core_data.time
                    LIMIT 1
                )
                WHERE EXISTS (
                    SELECT 1 FROM fueltech_extended_data e
                    WHERE e.session_id = fueltech_core_data.session_id
                      AND e.time = fueltech_core_data.time
                )
                """
            )
        )

    # 3) Add check constraints on unified fields (mirror of old extended constraints)
    op.create_check_constraint('chk_power_range', 'fueltech_core_data', '(estimated_power IS NULL OR (estimated_power >= 0 AND estimated_power <= 2000))')
    op.create_check_constraint('chk_torque_range', 'fueltech_core_data', '(estimated_torque IS NULL OR (estimated_torque >= 0 AND estimated_torque <= 5000))')
    op.create_check_constraint('chk_g_accel_range', 'fueltech_core_data', '(g_force_accel IS NULL OR (g_force_accel >= -7.0 AND g_force_accel <= 7.0))')
    op.create_check_constraint('chk_g_lateral_range', 'fueltech_core_data', '(g_force_lateral IS NULL OR (g_force_lateral >= -7.0 AND g_force_lateral <= 7.0))')

    # 4) Drop the fueltech_extended_data table
    op.drop_table('fueltech_extended_data')


def downgrade():
    """Recreate the extended table and move data back from core (best-effort)."""
    # Recreate fueltech_extended_data with original columns
    op.create_table(
        'fueltech_extended_data',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('session_id', sa.String(36), sa.ForeignKey('data_sessions.id'), nullable=False),
        sa.Column('time', sa.Float(), nullable=False),
        sa.Column('total_consumption', sa.Float()),
        sa.Column('average_consumption', sa.Float()),
        sa.Column('instant_consumption', sa.Float()),
        sa.Column('total_distance', sa.Float()),
        sa.Column('range', sa.Float()),
        sa.Column('estimated_power', sa.Integer()),
        sa.Column('estimated_torque', sa.Integer()),
        sa.Column('traction_speed', sa.Float()),
        sa.Column('acceleration_speed', sa.Float()),
        sa.Column('acceleration_distance', sa.Float()),
        sa.Column('traction_control_slip', sa.Float()),
        sa.Column('traction_control_slip_rate', sa.Integer()),
        sa.Column('delta_tps', sa.Float()),
        sa.Column('g_force_accel', sa.Float()),
        sa.Column('g_force_lateral', sa.Float()),
        sa.Column('g_force_accel_raw', sa.Float()),
        sa.Column('g_force_lateral_raw', sa.Float()),
        sa.Column('pitch_angle', sa.Float()),
        sa.Column('pitch_rate', sa.Float()),
        sa.Column('roll_angle', sa.Float()),
        sa.Column('roll_rate', sa.Float()),
        sa.Column('heading', sa.Float()),
        sa.Column('accel_enrichment', sa.String(10)),
        sa.Column('decel_enrichment', sa.String(10)),
        sa.Column('injection_cutoff', sa.String(10)),
        sa.Column('after_start_injection', sa.String(10)),
        sa.Column('start_button_toggle', sa.String(10)),
    )

    # Copy back data for rows that have non-null extended fields
    conn = op.get_bind()
    conn.execute(sa.text(
        """
        INSERT INTO fueltech_extended_data (
            id, session_id, time, total_consumption, average_consumption, instant_consumption,
            total_distance, range, estimated_power, estimated_torque, traction_speed,
            acceleration_speed, acceleration_distance, traction_control_slip, traction_control_slip_rate,
            delta_tps, g_force_accel, g_force_lateral, g_force_accel_raw, g_force_lateral_raw,
            pitch_angle, pitch_rate, roll_angle, roll_rate, heading,
            accel_enrichment, decel_enrichment, injection_cutoff, after_start_injection, start_button_toggle
        )
        SELECT 
            hex(randomblob(16)), session_id, time, total_consumption, average_consumption, instant_consumption,
            total_distance, range, estimated_power, estimated_torque, traction_speed,
            acceleration_speed, acceleration_distance, traction_control_slip, traction_control_slip_rate,
            delta_tps, g_force_accel, g_force_lateral, g_force_accel_raw, g_force_lateral_raw,
            pitch_angle, pitch_rate, roll_angle, roll_rate, heading,
            accel_enrichment, decel_enrichment, injection_cutoff, after_start_injection, start_button_toggle
        FROM fueltech_core_data
        WHERE 
            total_consumption IS NOT NULL OR average_consumption IS NOT NULL OR instant_consumption IS NOT NULL OR
            total_distance IS NOT NULL OR range IS NOT NULL OR estimated_power IS NOT NULL OR estimated_torque IS NOT NULL OR
            traction_speed IS NOT NULL OR acceleration_speed IS NOT NULL OR acceleration_distance IS NOT NULL OR
            traction_control_slip IS NOT NULL OR traction_control_slip_rate IS NOT NULL OR delta_tps IS NOT NULL OR
            g_force_accel IS NOT NULL OR g_force_lateral IS NOT NULL OR g_force_accel_raw IS NOT NULL OR g_force_lateral_raw IS NOT NULL OR
            pitch_angle IS NOT NULL OR pitch_rate IS NOT NULL OR roll_angle IS NOT NULL OR roll_rate IS NOT NULL OR heading IS NOT NULL OR
            accel_enrichment IS NOT NULL OR decel_enrichment IS NOT NULL OR injection_cutoff IS NOT NULL OR 
            after_start_injection IS NOT NULL OR start_button_toggle IS NOT NULL
        """
    ))

    # Drop the added columns from core (SQLite can't drop multiple easily; leaving for manual rollback if needed)
    # Note: Proper rollback would require table recreation; omitted for brevity.
