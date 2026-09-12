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
            "s3:PutObject"
        ]
        Resource = "${aws_s3_bucket.resland_user_resumes.arn}/*"
      }
    ]
  })
}

resource "aws_iam_user_policy_attachment" "resland_user_policy_attachment" {
  user = aws_iam_user.resland_user.name
  policy_arn = aws_iam_policy.resland_user_policy.arn
}
