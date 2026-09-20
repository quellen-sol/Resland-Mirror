#!/usr/bin/env -S node
import type { Contract as Start } from '../../snapshots/4cfa9de85dda60dd8eabf3b7d38fdfb73de17bf860102235b1e9c846e345aa23/contract';
import startContract from '../../snapshots/4cfa9de85dda60dd8eabf3b7d38fdfb73de17bf860102235b1e9c846e345aa23/contract.json' with { type: 'json' };
import type { Contract as End } from '../../snapshots/ab83bc9d635db30afd8840549bb14c2c7d6c3da024579d31bc5be53d1dc4a20f/contract';
import endContract from '../../snapshots/ab83bc9d635db30afd8840549bb14c2c7d6c3da024579d31bc5be53d1dc4a20f/contract.json' with { type: 'json' };
import {
  Migration,
  MigrationCLI,
  checkExpression,
  col,
  fn,
  lit,
  primaryKey,
} from '@prisma/orm-postgres/migration';
import postgresStatic from '@prisma/orm-postgres/static';

const statics = postgresStatic<End>({ contractJson: endContract });
const { raw } = statics;

export default class M extends Migration<Start, End> {
  override readonly startContractJson = startContract;
  override readonly endContractJson = endContract;

  override get operations() {
    return [
      this.createTable({
        schema: 'public',
        table: 'model_pricing',
        columns: [
          col('credits_per_1k_input', 'int4', {
            notNull: true,
            codecRef: { codecId: 'pg/int4@1' },
          }),
          col('credits_per_1k_output', 'int4', {
            notNull: true,
            codecRef: { codecId: 'pg/int4@1' },
          }),
          col('display_name', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('enabled', 'bool', {
            notNull: true,
            default: lit(true),
            codecRef: { codecId: 'pg/bool@1' },
          }),
          col('id', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('sort_order', 'int4', {
            notNull: true,
            default: lit(0),
            codecRef: { codecId: 'pg/int4@1' },
          }),
        ],
        constraints: [primaryKey(['id'])],
      }),
      this.createTable({
        schema: 'public',
        table: 'token_purchase',
        columns: [
          col('amount_cents', 'int4', { notNull: true, codecRef: { codecId: 'pg/int4@1' } }),
          col('created_at', 'timestamptz', {
            notNull: true,
            default: fn('now()'),
            codecRef: { codecId: 'pg/timestamptz-temporal@1' },
          }),
          col('credits', 'int4', { notNull: true, codecRef: { codecId: 'pg/int4@1' } }),
          col('currency', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('id', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('status', 'text', {
            notNull: true,
            default: lit('PENDING'),
            codecRef: { codecId: 'pg/text@1' },
          }),
          col('user_id', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
        ],
        constraints: [
          primaryKey(['id']),
          checkExpression(
            'token_purchase_status_check_37d7c798',
            "\"status\" IN ('PENDING', 'COMPLETED', 'EXPIRED')",
          ),
        ],
      }),
      this.createTable({
        schema: 'public',
        table: 'token_usage',
        columns: [
          col('created_at', 'timestamptz', {
            notNull: true,
            default: fn('now()'),
            codecRef: { codecId: 'pg/timestamptz-temporal@1' },
          }),
          col('credits_charged', 'int4', { notNull: true, codecRef: { codecId: 'pg/int4@1' } }),
          col('id', 'SERIAL', { notNull: true, codecRef: { codecId: 'pg/int4@1' } }),
          col('input_tokens', 'int4', { notNull: true, codecRef: { codecId: 'pg/int4@1' } }),
          col('job_id', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('job_kind', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('model', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('output_tokens', 'int4', { notNull: true, codecRef: { codecId: 'pg/int4@1' } }),
          col('user_id', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
        ],
        constraints: [
          primaryKey(['id']),
          checkExpression(
            'token_usage_job_kind_check_74df029d',
            "\"job_kind\" IN ('SUGGESTION', 'TAILOR')",
          ),
        ],
      }),
      this.addColumn({
        schema: 'public',
        table: 'user',
        column: col('site_admin', 'bool', {
          notNull: true,
          default: lit(false),
          codecRef: { codecId: 'pg/bool@1' },
        }),
      }),
      this.addColumn({
        schema: 'public',
        table: 'user',
        column: col('stripe_customer_id', 'text', { codecRef: { codecId: 'pg/text@1' } }),
      }),
      this.addColumn({
        schema: 'public',
        table: 'user',
        column: col('token_balance', 'int4', {
          notNull: true,
          default: lit(100000),
          codecRef: { codecId: 'pg/int4@1' },
        }),
      }),
      this.addColumn({
        schema: 'public',
        table: 'user_suggestion',
        column: col('model', 'text', { codecRef: { codecId: 'pg/text@1' } }),
      }),
      this.addColumn({
        schema: 'public',
        table: 'user_tailor_run',
        column: col('model', 'text', { codecRef: { codecId: 'pg/text@1' } }),
      }),
      this.createIndex({
        schema: 'public',
        table: 'token_purchase',
        index: 'token_purchase_user_id_idx_6c952402',
        columns: ['user_id'],
      }),
      this.createIndex({
        schema: 'public',
        table: 'token_usage',
        index: 'token_usage_created_at_idx_225d8c0f',
        columns: ['created_at'],
      }),
      this.createIndex({
        schema: 'public',
        table: 'token_usage',
        index: 'token_usage_user_id_idx_6c952402',
        columns: ['user_id'],
      }),
      this.addForeignKey({
        schema: 'public',
        table: 'token_purchase',
        foreignKey: {
          name: 'token_purchase_user_id_fkey',
          columns: ['user_id'],
          references: { schema: 'public', table: 'user', columns: ['auth0_id'] },
        },
      }),
      this.addForeignKey({
        schema: 'public',
        table: 'token_usage',
        foreignKey: {
          name: 'token_usage_user_id_fkey',
          columns: ['user_id'],
          references: { schema: 'public', table: 'user', columns: ['auth0_id'] },
        },
      }),
      // Seed the selectable-model catalog. 1 credit = $0.00001; rates are
      // roughly OpenRouter list price x1.25 per 1K tokens.
      this.dataTransform(statics.contract, 'seed-model_pricing-catalog', {
        check: () =>
          raw.sql`
            SELECT v.id FROM (VALUES
              ('openrouter:openai/gpt-5-mini'),
              ('openrouter:openai/gpt-5'),
              ('openrouter:anthropic/claude-sonnet-4.5'),
              ('openrouter:google/gemini-2.5-flash')
            ) AS v(id)
            WHERE NOT EXISTS (
              SELECT 1 FROM model_pricing mp WHERE mp.id = v.id
            )
          `.returnsRow({ id: 'pg/text@1' }),
        run: () =>
          raw.sql`
            INSERT INTO model_pricing
              (id, display_name, credits_per_1k_input, credits_per_1k_output, enabled, sort_order)
            VALUES
              ('openrouter:openai/gpt-5-mini', 'GPT-5 Mini', 30, 250, true, 1),
              ('openrouter:openai/gpt-5', 'GPT-5', 160, 1250, true, 2),
              ('openrouter:anthropic/claude-sonnet-4.5', 'Claude Sonnet 4.5', 375, 1900, true, 3),
              ('openrouter:google/gemini-2.5-flash', 'Gemini 2.5 Flash', 40, 315, true, 4)
            ON CONFLICT (id) DO NOTHING
          `.affectedCount(),
      }),
    ];
  }
}

MigrationCLI.run(import.meta.url, M);
