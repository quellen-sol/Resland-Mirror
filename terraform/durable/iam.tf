resource "aws_iam_user" "resland_user" {
  name = "resland-user"
}

resource "aws_iam_policy" "resland_user_policy" {
  name = "resland-user-policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
            "s3:PutObject",
            "s3:GetObject",
            "s3:DeleteObject"
        ]
        Resource = "${aws_s3_bucket.resland_user_resumes.arn}/*"
      },
      {
        # Account export and deletion list a user's files under
        # resumes/<auth0_id>/; without this, ListObjectsV2 is denied.
        # TODO: not applied to the live account yet. Apply this (terraform
        # apply in terraform/durable) before deploying /account export and
        # deletion, or both fail with a 502 at the S3 listing step.
        Effect   = "Allow"
        Action   = ["s3:ListBucket"]
        Resource = aws_s3_bucket.resland_user_resumes.arn
        Condition = {
          StringLike = { "s3:prefix" = ["resumes/*"] }
        }
      }
    ]
  })
}

resource "aws_iam_user_policy_attachment" "resland_user_policy_attachment" {
  user = aws_iam_user.resland_user.name
  policy_arn = aws_iam_policy.resland_user_policy.arn
}
