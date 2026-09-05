import asyncio
import asyncpg

async def check():
    try:
        conn = await asyncpg.connect("postgresql://dealflow_user:dealflow_password@localhost:5432/dealflow360")
        version = await conn.fetchval("SELECT version()")
        tables = await conn.fetch("""
            SELECT relname AS table_name, n_live_tup AS row_count
            FROM pg_stat_user_tables
            ORDER BY n_live_tup DESC
            LIMIT 25
        """)
        await conn.close()

        print("=" * 55)
        print("  DATABASE STATUS: CONNECTED ✅")
        print("=" * 55)
        print(f"  Server : {version[:55]}")
        print(f"  DB     : dealflow360")
        print("-" * 55)
        print(f"  {'TABLE':<35} {'ROWS':>8}")
        print("-" * 55)
        for t in tables:
            if t["row_count"] > 0:
                print(f"  {t['table_name']:<35} {t['row_count']:>8}")
        print("=" * 55)
    except Exception as e:
        print(f"  DATABASE STATUS: FAILED ❌")
        print(f"  Error: {e}")

asyncio.run(check())
