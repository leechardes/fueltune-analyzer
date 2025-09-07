"""Create fuel maps tables and relationships

Revision ID: fuel_maps_001
Revises: fuel_banks_001
Create Date: 2025-01-07 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.sqlite import JSON

# revision identifiers, used by Alembic.
revision = 'fuel_maps_001'
down_revision = 'fuel_banks_001'
branch_labels = None
depends_on = None


def upgrade():
    """Create all fuel maps tables."""
    
    # Tabela principal de mapas de injeção
    op.create_table('fuel_maps',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('vehicle_id', sa.String(36), sa.ForeignKey('vehicles.id'), nullable=False, comment='ID do veículo'),
        sa.Column('map_type', sa.String(50), nullable=False, comment='Tipo: main_fuel_2d_map, main_fuel_3d, etc'),
        sa.Column('bank_id', sa.String(1), nullable=True, comment='Bancada: A, B ou NULL para mapas compartilhados'),
        sa.Column('name', sa.String(100), nullable=False, comment='Nome do mapa'),
        sa.Column('description', sa.Text(), comment='Descrição detalhada'),
        sa.Column('dimensions', sa.Integer(), nullable=False, comment='1 para 2D, 2 para 3D'),
        sa.Column('x_axis_type', sa.String(50), nullable=False, comment='Tipo do eixo X: RPM, MAP, TEMP, TPS, VOLTAGE, TIME'),
        sa.Column('y_axis_type', sa.String(50), nullable=True, comment='Tipo do eixo Y (apenas para 3D)'),
        sa.Column('data_unit', sa.String(20), nullable=False, comment='Unidade dos dados: ms, %, degrees, lambda'),
        sa.Column('x_slots_total', sa.Integer(), nullable=False, default=32, comment='Total de slots no eixo X (máximo)'),
        sa.Column('x_slots_active', sa.Integer(), nullable=False, default=0, comment='Slots ativos no eixo X'),
        sa.Column('y_slots_total', sa.Integer(), nullable=False, default=32, comment='Total de slots no eixo Y (máximo)'),
        sa.Column('y_slots_active', sa.Integer(), nullable=False, default=0, comment='Slots ativos no eixo Y'),
        sa.Column('version', sa.Integer(), nullable=False, default=1, comment='Versão do mapa'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True, comment='Mapa está ativo'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), comment='Data de criação'),
        sa.Column('modified_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), comment='Última modificação'),
        sa.Column('modified_by', sa.String(100), comment='Usuário que fez a modificação'),
    )
    
    # Constraints e índices da tabela fuel_maps
    op.create_unique_constraint('uix_vehicle_map_bank', 'fuel_maps', ['vehicle_id', 'map_type', 'bank_id'])
    op.create_check_constraint('chk_dimensions_valid', 'fuel_maps', 'dimensions IN (1, 2)')
    op.create_check_constraint('chk_x_slots_valid', 'fuel_maps', 'x_slots_active <= x_slots_total')
    op.create_check_constraint('chk_y_slots_valid', 'fuel_maps', 'y_slots_active <= y_slots_total')
    op.create_check_constraint('chk_x_slots_positive', 'fuel_maps', 'x_slots_active >= 0')
    op.create_check_constraint('chk_y_slots_positive', 'fuel_maps', 'y_slots_active >= 0')
    op.create_check_constraint('chk_version_positive', 'fuel_maps', 'version >= 1')
    
    op.create_index('idx_vehicle_map_type', 'fuel_maps', ['vehicle_id', 'map_type'])
    op.create_index('idx_map_active', 'fuel_maps', ['is_active'])
    op.create_index('idx_map_bank', 'fuel_maps', ['bank_id'])
    op.create_index('idx_map_modified', 'fuel_maps', ['modified_at'])
    
    # Tabela de dados dos eixos
    op.create_table('map_axis_data',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('map_id', sa.String(36), sa.ForeignKey('fuel_maps.id'), nullable=False, comment='ID do mapa'),
        sa.Column('axis_type', sa.String(10), nullable=False, comment='Tipo do eixo: X ou Y'),
        sa.Column('data_type', sa.String(50), nullable=False, comment='Tipo de dados: RPM, MAP, TEMP, etc'),
        # 32 slots para todos os eixos
        sa.Column('slot_0', sa.Float(), comment='Slot 0'),
        sa.Column('slot_1', sa.Float(), comment='Slot 1'),
        sa.Column('slot_2', sa.Float(), comment='Slot 2'),
        sa.Column('slot_3', sa.Float(), comment='Slot 3'),
        sa.Column('slot_4', sa.Float(), comment='Slot 4'),
        sa.Column('slot_5', sa.Float(), comment='Slot 5'),
        sa.Column('slot_6', sa.Float(), comment='Slot 6'),
        sa.Column('slot_7', sa.Float(), comment='Slot 7'),
        sa.Column('slot_8', sa.Float(), comment='Slot 8'),
        sa.Column('slot_9', sa.Float(), comment='Slot 9'),
        sa.Column('slot_10', sa.Float(), comment='Slot 10'),
        sa.Column('slot_11', sa.Float(), comment='Slot 11'),
        sa.Column('slot_12', sa.Float(), comment='Slot 12'),
        sa.Column('slot_13', sa.Float(), comment='Slot 13'),
        sa.Column('slot_14', sa.Float(), comment='Slot 14'),
        sa.Column('slot_15', sa.Float(), comment='Slot 15'),
        sa.Column('slot_16', sa.Float(), comment='Slot 16'),
        sa.Column('slot_17', sa.Float(), comment='Slot 17'),
        sa.Column('slot_18', sa.Float(), comment='Slot 18'),
        sa.Column('slot_19', sa.Float(), comment='Slot 19'),
        sa.Column('slot_20', sa.Float(), comment='Slot 20'),
        sa.Column('slot_21', sa.Float(), comment='Slot 21'),
        sa.Column('slot_22', sa.Float(), comment='Slot 22'),
        sa.Column('slot_23', sa.Float(), comment='Slot 23'),
        sa.Column('slot_24', sa.Float(), comment='Slot 24'),
        sa.Column('slot_25', sa.Float(), comment='Slot 25'),
        sa.Column('slot_26', sa.Float(), comment='Slot 26'),
        sa.Column('slot_27', sa.Float(), comment='Slot 27'),
        sa.Column('slot_28', sa.Float(), comment='Slot 28'),
        sa.Column('slot_29', sa.Float(), comment='Slot 29'),
        sa.Column('slot_30', sa.Float(), comment='Slot 30'),
        sa.Column('slot_31', sa.Float(), comment='Slot 31'),
        sa.Column('active_slots', sa.Integer(), nullable=False, default=0, comment='Número de slots ativos'),
        sa.Column('min_value', sa.Float(), comment='Valor mínimo permitido'),
        sa.Column('max_value', sa.Float(), comment='Valor máximo permitido'),
    )
    
    op.create_index('idx_map_axis', 'map_axis_data', ['map_id', 'axis_type'])
    op.create_index('idx_axis_data_type', 'map_axis_data', ['data_type'])
    op.create_check_constraint('chk_active_slots_range', 'map_axis_data', 'active_slots >= 0 AND active_slots <= 32')
    op.create_check_constraint('chk_axis_type_valid', 'map_axis_data', "axis_type IN ('X', 'Y')")
    
    # Tabela de dados 2D
    op.create_table('map_data_2d',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('map_id', sa.String(36), sa.ForeignKey('fuel_maps.id'), nullable=False, comment='ID do mapa'),
        # 32 valores possíveis
        sa.Column('value_0', sa.Float(), comment='Valor 0'),
        sa.Column('value_1', sa.Float(), comment='Valor 1'),
        sa.Column('value_2', sa.Float(), comment='Valor 2'),
        sa.Column('value_3', sa.Float(), comment='Valor 3'),
        sa.Column('value_4', sa.Float(), comment='Valor 4'),
        sa.Column('value_5', sa.Float(), comment='Valor 5'),
        sa.Column('value_6', sa.Float(), comment='Valor 6'),
        sa.Column('value_7', sa.Float(), comment='Valor 7'),
        sa.Column('value_8', sa.Float(), comment='Valor 8'),
        sa.Column('value_9', sa.Float(), comment='Valor 9'),
        sa.Column('value_10', sa.Float(), comment='Valor 10'),
        sa.Column('value_11', sa.Float(), comment='Valor 11'),
        sa.Column('value_12', sa.Float(), comment='Valor 12'),
        sa.Column('value_13', sa.Float(), comment='Valor 13'),
        sa.Column('value_14', sa.Float(), comment='Valor 14'),
        sa.Column('value_15', sa.Float(), comment='Valor 15'),
        sa.Column('value_16', sa.Float(), comment='Valor 16'),
        sa.Column('value_17', sa.Float(), comment='Valor 17'),
        sa.Column('value_18', sa.Float(), comment='Valor 18'),
        sa.Column('value_19', sa.Float(), comment='Valor 19'),
        sa.Column('value_20', sa.Float(), comment='Valor 20'),
        sa.Column('value_21', sa.Float(), comment='Valor 21'),
        sa.Column('value_22', sa.Float(), comment='Valor 22'),
        sa.Column('value_23', sa.Float(), comment='Valor 23'),
        sa.Column('value_24', sa.Float(), comment='Valor 24'),
        sa.Column('value_25', sa.Float(), comment='Valor 25'),
        sa.Column('value_26', sa.Float(), comment='Valor 26'),
        sa.Column('value_27', sa.Float(), comment='Valor 27'),
        sa.Column('value_28', sa.Float(), comment='Valor 28'),
        sa.Column('value_29', sa.Float(), comment='Valor 29'),
        sa.Column('value_30', sa.Float(), comment='Valor 30'),
        sa.Column('value_31', sa.Float(), comment='Valor 31'),
    )
    
    op.create_index('idx_map_2d', 'map_data_2d', ['map_id'])
    
    # Criar a tabela 3D com apenas algumas colunas iniciais para não tornar a migration muito longa
    # O resto será adicionado via script Python separado
    op.create_table('map_data_3d',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('map_id', sa.String(36), sa.ForeignKey('fuel_maps.id'), nullable=False, comment='ID do mapa'),
        # Apenas as primeiras células como exemplo - o resto será criado via script
        sa.Column('value_0_0', sa.Float(), comment='Célula [0,0]'),
        sa.Column('value_0_1', sa.Float(), comment='Célula [0,1]'),
        sa.Column('value_0_2', sa.Float(), comment='Célula [0,2]'),
        sa.Column('value_0_3', sa.Float(), comment='Célula [0,3]'),
        sa.Column('value_0_4', sa.Float(), comment='Célula [0,4]'),
        sa.Column('value_0_5', sa.Float(), comment='Célula [0,5]'),
        # Adicionar as outras colunas restantes via script Python após esta migration
    )
    
    op.create_index('idx_map_3d', 'map_data_3d', ['map_id'])
    
    # Tabela de histórico de versões
    op.create_table('fuel_map_history',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('map_id', sa.String(36), sa.ForeignKey('fuel_maps.id'), nullable=False, comment='ID do mapa'),
        sa.Column('version', sa.Integer(), nullable=False, comment='Número da versão'),
        sa.Column('axis_data_snapshot', JSON(), comment='Snapshot dos dados dos eixos'),
        sa.Column('map_data_snapshot', JSON(), comment='Snapshot dos dados do mapa'),
        sa.Column('change_description', sa.Text(), comment='Descrição das alterações'),
        sa.Column('changed_by', sa.String(100), comment='Usuário que fez a alteração'),
        sa.Column('change_timestamp', sa.DateTime(), server_default=sa.func.now(), comment='Timestamp da alteração'),
        sa.Column('validation_status', sa.String(20), nullable=False, default='pending', comment='Status da validação'),
        sa.Column('quality_score', sa.Float(), comment='Pontuação de qualidade (0-100)'),
    )
    
    op.create_index('idx_map_version', 'fuel_map_history', ['map_id', 'version'])
    op.create_index('idx_history_timestamp', 'fuel_map_history', ['change_timestamp'])
    op.create_check_constraint('chk_history_version_positive', 'fuel_map_history', 'version >= 1')
    op.create_unique_constraint('uix_map_version', 'fuel_map_history', ['map_id', 'version'])
    
    # Tabela de templates de mapas
    op.create_table('map_templates',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False, comment='Nome do template'),
        sa.Column('description', sa.Text(), comment='Descrição detalhada'),
        sa.Column('engine_type', sa.String(50), comment='Tipo: Aspirado, Turbo, Supercharged'),
        sa.Column('fuel_type', sa.String(50), comment='Combustível: Gasolina, Etanol, Flex'),
        sa.Column('displacement_min', sa.Float(), comment='Cilindrada mínima em L'),
        sa.Column('displacement_max', sa.Float(), comment='Cilindrada máxima em L'),
        sa.Column('cylinders', sa.Integer(), comment='Número de cilindros'),
        sa.Column('default_bank_config', JSON(), comment='Configuração padrão das bancadas'),
        sa.Column('default_maps', JSON(), comment='Lista de mapas incluídos no template'),
        sa.Column('map_configurations', JSON(), comment='Configurações específicas de cada mapa'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('created_by', sa.String(100), comment='Criador do template'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True, comment='Template está ativo'),
        sa.Column('usage_count', sa.Integer(), nullable=False, default=0, comment='Número de usos do template'),
    )
    
    op.create_index('idx_template_name', 'map_templates', ['name'])
    op.create_index('idx_template_engine', 'map_templates', ['engine_type'])
    op.create_index('idx_template_fuel', 'map_templates', ['fuel_type'])
    op.create_index('idx_template_active', 'map_templates', ['is_active'])


def downgrade():
    """Drop all fuel maps tables."""
    
    # Dropar tabelas em ordem reversa (devido às foreign keys)
    op.drop_table('map_templates')
    op.drop_table('fuel_map_history')
    op.drop_table('map_data_3d')
    op.drop_table('map_data_2d')
    op.drop_table('map_axis_data')
    op.drop_table('fuel_maps')