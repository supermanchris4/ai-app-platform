output "schedule_name" {
  description = "The schedule's name."
  value       = aws_scheduler_schedule.this.name
}
