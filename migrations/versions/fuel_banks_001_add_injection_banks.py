"""Add fuel injection banks configuration to Vehicle model

Revision ID: fuel_banks_001
Revises: 20c1d4d1f5bb
Create Date: 2025-01-07 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.sqlite import JSON

# revision identifiers, used by Alembic.
revision = 'fuel_banks_001'
down_revision = '20c1d4d1f5bb'
branch_labels = None
depends_on = None


def upgrade():
    """Add fuel injection banks configuration fields to vehicles table."""
    
    # Adicionar campos da Bancada A
    op.add_column('vehicles', sa.Column('bank_a_enabled', sa.Boolean(), nullable=True, comment='Bancada A habilitada (sempre ativa)'))
    op.add_column('vehicles', sa.Column('bank_a_mode', sa.String(length=20), nullable=True, comment='Modo: multiponto, semissequencial, sequencial'))
    op.add_column('vehicles', sa.Column('bank_a_outputs', JSON(), nullable=True, comment='Lista de saídas utilizadas: [1, 2, 3, 4] etc'))
    op.add_column('vehicles', sa.Column('bank_a_injector_flow', sa.Float(), nullable=True, comment='Vazão por bico em lb/h'))
    op.add_column('vehicles', sa.Column('bank_a_injector_count', sa.Integer(), nullable=True, comment='Quantidade de bicos na bancada A'))
    op.add_column('vehicles', sa.Column('bank_a_total_flow', sa.Float(), nullable=True, comment='Vazão total calculada (lb/h)'))
    op.add_column('vehicles', sa.Column('bank_a_dead_time', sa.Float(), nullable=True, comment='Dead time dos injetores em ms'))
    
    # Adicionar campos da Bancada B
    op.add_column('vehicles', sa.Column('bank_b_enabled', sa.Boolean(), nullable=True, comment='Bancada B habilitada'))
    op.add_column('vehicles', sa.Column('bank_b_mode', sa.String(length=20), nullable=True, comment='Modo: multiponto, semissequencial, sequencial'))
    op.add_column('vehicles', sa.Column('bank_b_outputs', JSON(), nullable=True, comment='Lista de saídas utilizadas: [5, 6, 7, 8] etc'))
    op.add_column('vehicles', sa.Column('bank_b_injector_flow', sa.Float(), nullable=True, comment='Vazão por bico em lb/h'))
    op.add_column('vehicles', sa.Column('bank_b_injector_count', sa.Integer(), nullable=True, comment='Quantidade de bicos na bancada B'))
    op.add_column('vehicles', sa.Column('bank_b_total_flow', sa.Float(), nullable=True, comment='Vazão total calculada (lb/h)'))
    op.add_column('vehicles', sa.Column('bank_b_dead_time', sa.Float(), nullable=True, comment='Dead time dos injetores em ms'))
    
    # Adicionar limites operacionais
    op.add_column('vehicles', sa.Column('max_map_pressure', sa.Float(), nullable=True, comment='Pressão MAP máxima em bar'))
    op.add_column('vehicles', sa.Column('min_map_pressure', sa.Float(), nullable=True, comment='Pressão MAP mínima em bar'))
    
    # Definir valores padrão para registros existentes
    op.execute("UPDATE vehicles SET bank_a_enabled = 1 WHERE bank_a_enabled IS NULL")
    op.execute("UPDATE vehicles SET bank_a_mode = 'semissequencial' WHERE bank_a_mode IS NULL")
    op.execute("UPDATE vehicles SET bank_b_enabled = 0 WHERE bank_b_enabled IS NULL")
    op.execute("UPDATE vehicles SET bank_b_mode = 'semissequencial' WHERE bank_b_mode IS NULL")
    op.execute("UPDATE vehicles SET max_map_pressure = 5.0 WHERE max_map_pressure IS NULL")
    op.execute("UPDATE vehicles SET min_map_pressure = -1.0 WHERE min_map_pressure IS NULL")
    
    # Tornar campos obrigatórios após definir valores padrão
    op.alter_column('vehicles', 'bank_a_enabled', nullable=False, server_default='1')
    op.alter_column('vehicles', 'bank_a_mode', nullable=False, server_default='semissequencial')
    op.alter_column('vehicles', 'bank_b_enabled', nullable=False, server_default='0')
    op.alter_column('vehicles', 'bank_b_mode', nullable=False, server_default='semissequencial')
    op.alter_column('vehicles', 'max_map_pressure', nullable=False, server_default='5.0')
    op.alter_column('vehicles', 'min_map_pressure', nullable=False, server_default='-1.0')


def downgrade():
    """Remove fuel injection banks configuration fields from vehicles table."""
    
    # Remover campos da Bancada A
    op.drop_column('vehicles', 'bank_a_enabled')
    op.drop_column('vehicles', 'bank_a_mode')
    op.drop_column('vehicles', 'bank_a_outputs')
    op.drop_column('vehicles', 'bank_a_injector_flow')
    op.drop_column('vehicles', 'bank_a_injector_count')
    op.drop_column('vehicles', 'bank_a_total_flow')
    op.drop_column('vehicles', 'bank_a_dead_time')
    
    # Remover campos da Bancada B
    op.drop_column('vehicles', 'bank_b_enabled')
    op.drop_column('vehicles', 'bank_b_mode')
    op.drop_column('vehicles', 'bank_b_outputs')
    op.drop_column('vehicles', 'bank_b_injector_flow')
    op.drop_column('vehicles', 'bank_b_injector_count')
    op.drop_column('vehicles', 'bank_b_total_flow')
    op.drop_column('vehicles', 'bank_b_dead_time')
    
    # Remover limites operacionais
    op.drop_column('vehicles', 'max_map_pressure')
    op.drop_column('vehicles', 'min_map_pressure')