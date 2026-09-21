resource "aws_s3_bucket" "resland_user_resumes" {
  bucket = "resland-user-resumes"
}

output "bucket_name" {
  value = aws_s3_bucket.resland_user_resumes.bucket
}
