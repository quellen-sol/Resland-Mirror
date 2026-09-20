#!/usr/bin/env -S node
import type { Contract as Start } from '../../snapshots/2ebc10a638e3daa23818a89dda5ef8edbc44a3a68f2cdcfb1ee01d700cf1c472/contract';
import startContract from '../../snapshots/2ebc10a638e3daa23818a89dda5ef8edbc44a3a68f2cdcfb1ee01d700cf1c472/contract.json' with { type: 'json' };
import type { Contract as End } from '../../snapshots/c922ffdeabd27a01d3cd2f3cabddfef92dd43eaf63acabacad4c2f2df8d84ecb/contract';
import endContract from '../../snapshots/c922ffdeabd27a01d3cd2f3cabddfef92dd43eaf63acabacad4c2f2df8d84ecb/contract.json' with { type: 'json' };
import { Migration, MigrationCLI, col } from '@prisma/orm-postgres/migration';
import postgresStatic from '@prisma/orm-postgres/static';

const statics = postgresStatic<End>({ contractJson: endContract });
const { sql, raw } = statics;

export default class M extends Migration<Start, End> {
  override readonly startContractJson = startContract;
  override readonly endContractJson = endContract;

  override get operations() {
    return [
      this.addColumn({
        schema: 'public',
        table: 'user_base_experience_bullet',
        column: col('bullet_order', 'int4', { codecRef: { codecId: 'pg/int4@1' } }),
      }),
      this.dataTransform(statics.contract, 'backfill-user_base_experience_bullet-bullet_order', {
        check: () =>
          sql.public.user_base_experience_bullet
            .select('id')
            .where((f, fns) => fns.eq(f.bullet_order, null))
            .limit(1),
        run: () =>
          raw.sql`
            UPDATE user_base_experience_bullet AS t
            SET bullet_order = s.rn - 1
            FROM (
              SELECT id, ROW_NUMBER() OVER (PARTITION BY user_experience_id ORDER BY id) AS rn
              FROM user_base_experience_bullet
            ) AS s
            WHERE s.id = t.id AND t.bullet_order IS NULL
          `.affectedCount(),
      }),
      this.setNotNull({
        schema: 'public',
        table: 'user_base_experience_bullet',
        column: 'bullet_order',
      }),
      this.createIndex({
        schema: 'public',
        table: 'user_base_experience_bullet',
        index: 'bullet_exp_order_idx',
        columns: ['user_experience_id', 'bullet_order'],
      }),
    ];
  }
}

MigrationCLI.run(import.meta.url, M);
