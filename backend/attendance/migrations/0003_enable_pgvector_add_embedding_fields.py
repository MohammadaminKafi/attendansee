# Generated migration for pgvector support

from django.db import migrations, models, connection
import pgvector.django


def enable_vector_extension(apps, schema_editor):
    """
    Enable pgvector extension.
    
    In test environments, conftest.py creates the extension before migrations.
    In production/development, this function creates it.
    """
    db_name = connection.settings_dict.get('NAME', '')
    
    # In test mode, extension should already exist from conftest.py
    # Just try to create it anyway - IF NOT EXISTS makes it safe
    with schema_editor.connection.cursor() as cursor:
        cursor.execute('CREATE EXTENSION IF NOT EXISTS vector;')


def disable_vector_extension(apps, schema_editor):
    """
    Disable pgvector extension on migration rollback.
    
    Note: In test environments, we don't drop the extension as it's
    managed by the test session setup.
    """
    db_name = connection.settings_dict.get('NAME', '')
    
    # Skip dropping in test mode
    if db_name.startswith('test_') or 'test' in db_name.lower():
        return
    
    # Production/Development: Drop extension
    with schema_editor.connection.cursor() as cursor:
        cursor.execute('DROP EXTENSION IF EXISTS vector;')


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0002_alter_facecrop_crop_image_path_and_more'),
    ]

    operations = [
        # Enable pgvector extension with graceful error handling
        migrations.RunPython(
            enable_vector_extension,
            reverse_code=disable_vector_extension
        ),
        
        # Add embedding field to FaceCrop
        migrations.AddField(
            model_name='facecrop',
            name='embedding',
            field=pgvector.django.VectorField(
                blank=True,
                dimensions=512,
                help_text='Face embedding vector for similarity search',
                null=True
            ),
        ),
        
        # Add embedding_model field to FaceCrop
        migrations.AddField(
            model_name='facecrop',
            name='embedding_model',
            field=models.CharField(
                blank=True,
                choices=[
                    ('facenet', 'FaceNet (128D)'),
                    ('arcface', 'ArcFace (512D)')
                ],
                help_text='Model used to generate the embedding',
                max_length=20,
                null=True
            ),
        ),
        
        # Add index on embedding_model field
        migrations.AddIndex(
            model_name='facecrop',
            index=models.Index(fields=['embedding_model'], name='face_crops_embeddi_idx'),
        ),
        
        # Add index for vector similarity search using HNSW (Hierarchical Navigable Small World)
        # This significantly speeds up nearest neighbor searches
        # Note: This will be skipped in test environments without pgvector
        migrations.RunSQL(
            sql="""
                DO $$ 
                BEGIN
                    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
                        CREATE INDEX IF NOT EXISTS face_crops_embedding_hnsw_idx 
                        ON face_crops 
                        USING hnsw (embedding vector_cosine_ops);
                    END IF;
                END $$;
            """,
            reverse_sql="""
                DROP INDEX IF EXISTS face_crops_embedding_hnsw_idx;
            """
        ),
    ]
