import time
import random
import logging
from django_task_queue.task_registry import task_registry

logger = logging.getLogger(__name__)


@task_registry.register('add_numbers')
def add_numbers(a: int, b: int) -> int:
    """
    Task đơn giản để cộng hai số
    
    Args:
        a: Số thứ nhất
        b: Số thứ hai
        
    Returns:
        Tổng của a và b
    """
    logger.info(f"Adding {a} + {b}")
    result = a + b
    logger.info(f"Result: {result}")
    return result


@task_registry.register('multiply_numbers')
def multiply_numbers(a: int, b: int) -> int:
    """
    Task đơn giản để nhân hai số
    
    Args:
        a: Số thứ nhất
        b: Số thứ hai
        
    Returns:
        Tích của a và b
    """
    logger.info(f"Multiplying {a} * {b}")
    result = a * b
    logger.info(f"Result: {result}")
    return result


@task_registry.register('slow_task')
def slow_task(duration: int = 5, message: str = "Processing...") -> str:
    """
    Task chạy chậm để test timeout và monitoring
    
    Args:
        duration: Thời gian chạy (seconds)
        message: Thông điệp để log
        
    Returns:
        Thông điệp hoàn thành
    """
    logger.info(f"Starting slow task: {message} (duration: {duration}s)")
    
    for i in range(duration):
        time.sleep(1)
        logger.info(f"Progress: {i+1}/{duration}")
    
    result = f"Completed: {message} after {duration} seconds"
    logger.info(result)
    return result


@task_registry.register('random_task')
def random_task(min_val: int = 1, max_val: int = 100) -> dict:
    """
    Task tạo số ngẫu nhiên và thực hiện một số tính toán
    
    Args:
        min_val: Giá trị tối thiểu
        max_val: Giá trị tối đa
        
    Returns:
        Dictionary chứa kết quả
    """
    logger.info(f"Generating random number between {min_val} and {max_val}")
    
    number = random.randint(min_val, max_val)
    square = number ** 2
    is_even = number % 2 == 0
    
    result = {
        "number": number,
        "square": square,
        "is_even": is_even,
        "range": f"{min_val}-{max_val}"
    }
    
    logger.info(f"Generated result: {result}")
    return result


@task_registry.register('failing_task')
def failing_task(should_fail: bool = True, error_message: str = "Task failed intentionally") -> str:
    """
    Task có thể thất bại để test retry mechanism
    
    Args:
        should_fail: Có nên thất bại không
        error_message: Thông điệp lỗi
        
    Returns:
        Thông điệp thành công
        
    Raises:
        Exception: Nếu should_fail = True
    """
    logger.info(f"Running failing task (should_fail: {should_fail})")
    
    if should_fail:
        logger.error(f"Task failing: {error_message}")
        raise Exception(error_message)
    
    result = "Task completed successfully"
    logger.info(result)
    return result


@task_registry.register('process_data')
def process_data(data: list, operation: str = "sum") -> dict:
    """
    Task xử lý dữ liệu với các operation khác nhau
    
    Args:
        data: List các số để xử lý
        operation: Loại operation (sum, avg, max, min)
        
    Returns:
        Dictionary chứa kết quả
    """
    logger.info(f"Processing data with operation: {operation}")
    logger.info(f"Data: {data}")
    
    if not data:
        raise ValueError("Data list cannot be empty")
    
    if not all(isinstance(x, (int, float)) for x in data):
        raise ValueError("All data items must be numbers")
    
    result = {"operation": operation, "data_count": len(data)}
    
    if operation == "sum":
        result["result"] = sum(data)
    elif operation == "avg":
        result["result"] = sum(data) / len(data)
    elif operation == "max":
        result["result"] = max(data)
    elif operation == "min":
        result["result"] = min(data)
    else:
        raise ValueError(f"Unsupported operation: {operation}")
    
    logger.info(f"Processing result: {result}")
    return result


@task_registry.register('send_notification')
def send_notification(recipient: str, message: str, notification_type: str = "email") -> dict:
    """
    Task mô phỏng gửi notification
    
    Args:
        recipient: Người nhận
        message: Nội dung thông báo
        notification_type: Loại thông báo (email, sms, push)
        
    Returns:
        Dictionary chứa thông tin gửi
    """
    logger.info(f"Sending {notification_type} notification to {recipient}")
    
    # Simulate processing time
    time.sleep(random.uniform(0.5, 2.0))
    
    # Simulate random failure (10% chance)
    if random.random() < 0.1:
        raise Exception(f"Failed to send {notification_type} to {recipient}")
    
    result = {
        "recipient": recipient,
        "message": message,
        "type": notification_type,
        "status": "sent",
        "timestamp": time.time()
    }
    
    logger.info(f"Notification sent successfully: {result}")
    return result 