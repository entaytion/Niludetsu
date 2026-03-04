from .supabase_database import SupabaseDatabase, database

Database = SupabaseDatabase  # ← даём алиас и тут тоже

__all__ = ["SupabaseDatabase", "Database", "database"]

