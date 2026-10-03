#!/usr/bin/env -S node
import type { Contract as End } from '../../snapshots/4dbd015ad3e021f63ef04bfa31778f34a218409bd517c766541be7427453a580/contract';
import endContract from '../../snapshots/4dbd015ad3e021f63ef04bfa31778f34a218409bd517c766541be7427453a580/contract.json' with { type: 'json' };
import type { Contract as Start } from '../../snapshots/bc3ed381debcbee76352fb5ba436fd0db987dc694f94fc7a46913c0dc559498e/contract';
import startContract from '../../snapshots/bc3ed381debcbee76352fb5ba436fd0db987dc694f94fc7a46913c0dc559498e/contract.json' with { type: 'json' };
import {
  Migration,
  MigrationCLI,
  checkExpression,
  col,
  fn,
  lit,
  primaryKey,
} from '@prisma/orm-postgres/migration';

export default class M extends Migration<Start, End> {
  override readonly startContractJson = startContract;
  override readonly endContractJson = endContract;

  override get operations() {
    return [
      this.dropCheckConstraint({
        schema: 'public',
        table: 'token_usage',
        constraint: 'token_usage_job_kind_check_74df029d',
      }),
      this.createTable({
        schema: 'public',
        table: 'system_design_message',
        columns: [
          col('content', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('created_at', 'timestamptz', {
            notNull: true,
            default: fn('now()'),
            codecRef: { codecId: 'pg/timestamptz-temporal@1' },
          }),
          col('id', 'SERIAL', { notNull: true, codecRef: { codecId: 'pg/int4@1' } }),
          col('phase', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('role', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('session_id', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
        ],
        constraints: [
          primaryKey(['id']),
          checkExpression(
            'system_design_message_phase_check_affcc3a8',
            "\"phase\" IN ('REQUIREMENTS', 'ESTIMATION', 'HIGH_LEVEL_DESIGN', 'DEEP_DIVE', 'FEEDBACK')",
          ),
          checkExpression(
            'system_design_message_role_check_c450733a',
            "\"role\" IN ('INTERVIEWER', 'CANDIDATE')",
          ),
        ],
      }),
      this.createTable({
        schema: 'public',
        table: 'user_system_design_session',
        columns: [
          col('agent_context', 'text', { codecRef: { codecId: 'pg/text@1' } }),
          col('brief', 'text', { codecRef: { codecId: 'pg/text@1' } }),
          col('company_name', 'text', { codecRef: { codecId: 'pg/text@1' } }),
          col('completed_at', 'timestamptz', {
            codecRef: { codecId: 'pg/timestamptz-temporal@1' },
          }),
          col('created_at', 'timestamptz', {
            notNull: true,
            default: fn('now()'),
            codecRef: { codecId: 'pg/timestamptz-temporal@1' },
          }),
          col('diagram', 'text', {
            notNull: true,
            default: lit('[]'),
            codecRef: { codecId: 'pg/text@1' },
          }),
          col('estimates', 'text', {
            notNull: true,
            default: lit(''),
            codecRef: { codecId: 'pg/text@1' },
          }),
          col('hire_signal', 'text', { codecRef: { codecId: 'pg/text@1' } }),
          col('id', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('job_description', 'text', { codecRef: { codecId: 'pg/text@1' } }),
          col('last_turn_id', 'text', { codecRef: { codecId: 'pg/text@1' } }),
          col('letter_grade', 'text', { codecRef: { codecId: 'pg/text@1' } }),
          col('level', 'text', {
            notNull: true,
            default: lit('SENIOR'),
            codecRef: { codecId: 'pg/text@1' },
          }),
          col('model', 'text', { codecRef: { codecId: 'pg/text@1' } }),
          col('notice', 'text', { codecRef: { codecId: 'pg/text@1' } }),
          col('phase', 'text', {
            notNull: true,
            default: lit('REQUIREMENTS'),
            codecRef: { codecId: 'pg/text@1' },
          }),
          col('phase_durations', 'text', {
            notNull: true,
            default: lit('{}'),
            codecRef: { codecId: 'pg/text@1' },
          }),
          col('phase_started_at', 'timestamptz', {
            notNull: true,
            default: fn('now()'),
            codecRef: { codecId: 'pg/timestamptz-temporal@1' },
          }),
          col('problem_id', 'text', { codecRef: { codecId: 'pg/text@1' } }),
          col('prompt', 'text', { codecRef: { codecId: 'pg/text@1' } }),
          col('requirements', 'text', {
            notNull: true,
            default: lit(''),
            codecRef: { codecId: 'pg/text@1' },
          }),
          col('result', 'text', { codecRef: { codecId: 'pg/text@1' } }),
          col('role', 'text', { codecRef: { codecId: 'pg/text@1' } }),
          col('source', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
          col('status', 'text', {
            notNull: true,
            default: lit('PROCESSING'),
            codecRef: { codecId: 'pg/text@1' },
          }),
          col('tailored_resume_id', 'text', { codecRef: { codecId: 'pg/text@1' } }),
          col('title', 'text', { codecRef: { codecId: 'pg/text@1' } }),
          col('user_id', 'text', { notNull: true, codecRef: { codecId: 'pg/text@1' } }),
        ],
        constraints: [
          primaryKey(['id']),
          checkExpression(
            'user_system_design_session_level_check_a955ca61',
            "\"level\" IN ('MID', 'SENIOR', 'STAFF')",
          ),
          checkExpression(
            'user_system_design_session_phase_check_affcc3a8',
            "\"phase\" IN ('REQUIREMENTS', 'ESTIMATION', 'HIGH_LEVEL_DESIGN', 'DEEP_DIVE', 'FEEDBACK')",
          ),
          checkExpression(
            'user_system_design_session_source_check_e9786979',
            "\"source\" IN ('BANK', 'JOB')",
          ),
          checkExpression(
            'user_system_design_session_status_check_fa868dec',
            "\"status\" IN ('PROCESSING', 'WAITING_FOR_INPUT', 'COMPLETED', 'FAILED')",
          ),
        ],
      }),
      this.addCheckConstraint({
        schema: 'public',
        table: 'token_usage',
        constraint: 'token_usage_job_kind_check_2fbdeefd',
        expression: "\"job_kind\" IN ('SUGGESTION', 'TAILOR', 'SYSTEM_DESIGN')",
      }),
      this.createIndex({
        schema: 'public',
        table: 'system_design_message',
        index: 'system_design_message_session_id_idx_00ba47bf',
        columns: ['session_id'],
      }),
      this.createIndex({
        schema: 'public',
        table: 'user_system_design_session',
        index: 'user_system_design_session_user_id_idx_6c952402',
        columns: ['user_id'],
      }),
      this.addForeignKey({
        schema: 'public',
        table: 'system_design_message',
        foreignKey: {
          name: 'system_design_message_session_id_fkey',
          columns: ['session_id'],
          references: { schema: 'public', table: 'user_system_design_session', columns: ['id'] },
        },
      }),
      this.addForeignKey({
        schema: 'public',
        table: 'user_system_design_session',
        foreignKey: {
          name: 'user_system_design_session_user_id_fkey',
          columns: ['user_id'],
          references: { schema: 'public', table: 'user', columns: ['auth0_id'] },
        },
      }),
    ];
  }
}

MigrationCLI.run(import.meta.url, M);
