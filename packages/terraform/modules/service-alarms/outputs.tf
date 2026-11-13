output "alarm_names" {
  description = "The service's alarms, by what they watch."
  value = {
    running_tasks = aws_cloudwatch_metric_alarm.running_tasks.alarm_name
    cpu           = aws_cloudwatch_metric_alarm.cpu.alarm_name
    memory        = aws_cloudwatch_metric_alarm.memory.alarm_name
    server_errors = aws_cloudwatch_metric_alarm.server_errors.alarm_name
    response_time = aws_cloudwatch_metric_alarm.response_time.alarm_name
  }
}
