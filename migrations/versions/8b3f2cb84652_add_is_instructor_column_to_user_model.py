"""Add is_instructor column to User model and instructor_id to Course model

Revision ID: 8b3f2cb84652
Revises: 
Create Date: 2024-10-18 15:47:14.336770

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '8b3f2cb84652'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add is_instructor column to user table
    op.add_column('user', sa.Column('is_instructor', sa.Boolean(), nullable=True, server_default='false'))

    # Add instructor_id column to course table as nullable
    op.add_column('course', sa.Column('instructor_id', sa.Integer(), nullable=True))

    # Create a default instructor (you may want to change this to a specific user ID)
    op.execute("INSERT INTO \"user\" (username, email, password_hash, is_admin, is_instructor) VALUES ('default_instructor', 'default@example.com', 'placeholder_hash', false, true) ON CONFLICT DO NOTHING")
    
    # Set the default instructor for existing courses
    op.execute("UPDATE course SET instructor_id = (SELECT id FROM \"user\" WHERE username = 'default_instructor') WHERE instructor_id IS NULL")

    # Make instructor_id non-nullable
    op.alter_column('course', 'instructor_id', nullable=False)

    # Add foreign key constraint
    op.create_foreign_key(None, 'course', 'user', ['instructor_id'], ['id'])


def downgrade():
    # Remove foreign key constraint
    op.drop_constraint(None, 'course', type_='foreignkey')

    # Drop instructor_id column from course table
    op.drop_column('course', 'instructor_id')

    # Drop is_instructor column from user table
    op.drop_column('user', 'is_instructor')

    # Remove the default instructor
    op.execute("DELETE FROM \"user\" WHERE username = 'default_instructor'")
