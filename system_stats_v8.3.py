import logging
import time
import psutil
import os
import subprocess
import RPi.GPIO as GPIO
from waveshare_epd import epd4in2_V2
from PIL import Image, ImageDraw, ImageFont

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Get the directory where the script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Initialize previous network counters
prev_bytes_sent = 0
prev_bytes_recv = 0
prev_time = time.time()

# Debug GPIO setup
logger.debug("Attempting to set GPIO mode...")
try:
    GPIO.setmode(GPIO.BCM)
    logger.debug("GPIO mode set successfully")
except Exception as e:
    logger.error(f"Failed to set GPIO mode: {e}")
    raise

# Get the original user's home directory even when running with sudo
def get_original_user_home():
    """Get the home directory of the original user, even when running with sudo."""
    try:
        # Try to get the original user from SUDO_USER environment variable
        original_user = os.environ.get('SUDO_USER')
        if original_user:
            return f"/home/{original_user}"
    except:
        pass
    return os.path.expanduser('~')

HOME_DIR = get_original_user_home()

def find_font(font_name):
    """Search for a font in multiple locations."""
    possible_paths = [
        os.path.join(SCRIPT_DIR, "fonts", font_name),
        os.path.join(HOME_DIR, "fonts", font_name),
        os.path.join(SCRIPT_DIR, font_name),
        os.path.join(HOME_DIR, font_name),
        os.path.join("/usr/local/share/fonts/TTF", font_name),
        os.path.join("/usr/share/fonts/truetype", font_name)
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    raise FileNotFoundError(f"Font not found: {font_name}. Please ensure the font is in one of these locations: {', '.join(possible_paths)}")

def read_backup_status(file_path="/home/pi/backup_status.txt"):
    try:
        with open(file_path, 'r') as f:
            return f.read().strip()
    except Exception as e:
        logging.error(f"Failed to read backup status: {e}")
        return "No Status Available"

def get_cpu_temperature():
    """Get CPU temperature using vcgencmd (Raspberry Pi)."""
    try:
        temp_output = subprocess.check_output(["vcgencmd", "measure_temp"]).decode("utf-8")
        return temp_output.split("=")[1].strip()  # Extracts temperature
    except Exception as e:
        logging.error(f"Failed to get temperature: {e}")
        return "N/A"

def get_disk_usage(path):
    """Get disk usage for a specific mount point."""
    disk = psutil.disk_usage(path)
    used = disk.used // (1024 * 1024 * 1024)  # Convert to GB
    total = disk.total // (1024 * 1024 * 1024)  # Convert to GB
    return used, total

def get_system_stats():
    """Gather system statistics."""
    global prev_bytes_sent, prev_bytes_recv, prev_time
    
    current_time = time.time()
    net_io = psutil.net_io_counters()
    
    # Calculate network rate in MB/s
    time_delta = current_time - prev_time
    bytes_sent_delta = net_io.bytes_sent - prev_bytes_sent
    bytes_recv_delta = net_io.bytes_recv - prev_bytes_recv
    
    # Update previous values
    prev_bytes_sent = net_io.bytes_sent
    prev_bytes_recv = net_io.bytes_recv
    prev_time = current_time
    
    # Calculate rate in MB/s
    net_rate = (bytes_sent_delta + bytes_recv_delta) / 1024 / 1024 / time_delta

    cpu_usage = psutil.cpu_percent(interval=1)
    temp = get_cpu_temperature()
    root_used, root_total = get_disk_usage("/")
    nvme0_used, nvme0_total = get_disk_usage("/mnt/nvme0")
    nvme1_used, nvme1_total = get_disk_usage("/mnt/nvme1")

    # Format network value to show MB/s with proper formatting
    net_value = f"{net_rate:.1f} MB/s"

    return {
        "Network": net_value,
        "CPU": cpu_usage,
        "Temp": temp,
        "RootDisk": (root_used, root_total),
        "BK0": (nvme0_used, nvme0_total),
        "BK1": (nvme1_used, nvme1_total)
    }

def draw_dithered_bar(draw, x, y, width, height, percentage):
    """Draw a dithered progress bar with an outline."""
    bar_width = int((percentage / 100) * width)
    draw.rectangle([x, y, x + width, y + height], outline=255, fill=0)  # Outline
    for i in range(x, x + bar_width, 2):  # Dithered effect
        draw.line([(i, y), (i, y + height)], fill=255)

def display_stats(epd):
    """Draw system stats on the e-paper display with partial refresh."""
    # Initialize image and draw object
    image = Image.new('1', (epd.width, epd.height), 0)  # Black background
    draw = ImageDraw.Draw(image)

    # Load fonts from local directory
    header_font_path = os.path.join(SCRIPT_DIR, "fonts", "DotMatrixTwoExtended.ttf")
    body_font_path = os.path.join(SCRIPT_DIR, "fonts", "Perfect_DOS_VGA_437.ttf")

    # Verify fonts exist
    if not os.path.exists(header_font_path):
        raise FileNotFoundError(f"Header font not found: {header_font_path}")
    if not os.path.exists(body_font_path):
        raise FileNotFoundError(f"Body font not found: {body_font_path}")

    font_large = ImageFont.truetype(header_font_path, 28)
    font_small = ImageFont.truetype(body_font_path, 18)
    font_mono = ImageFont.truetype(body_font_path, 18)

    # Draw static elements (header and labels)
    header_text = "=== SnapSync ==="
    header_width, header_height = draw.textbbox((0, 0), header_text, font=font_large)[2:]
    center_x = (epd.width - header_width) // 2

    draw.rectangle((0, 0, epd.width, header_height + 16), fill=0)  # Black header background
    draw.text((center_x, 8), header_text, font=font_large, fill=255)  # White text

    # Static Section headers
    y_offset = header_height + 24
    label_x = 10
    bar_x = 80
    bar_width = 200
    value_x = 290

    # Labels for CPU, Root, BK0, BK1
    for label in ["[CPU]", "[ROOT]", "[BK0]", "[BK1]"]:
        draw.text((label_x, y_offset), label, font=font_small, fill=255)
        y_offset += 25

    # Labels for TEMP and NET (below IMM)
    draw.text((label_x, y_offset), "[TEMP]", font=font_small, fill=255)
    y_offset += 25
    draw.text((label_x, y_offset), "[NET]", font=font_small, fill=255)

    # Backup text (with extra space above)
    backup_status_y = y_offset + 50  # Increased space above backup status

    # Full display update for static elements
    epd.display(epd.getbuffer(image))
    epd.init()  # Re-initialize for partial updates

    partial_refresh_count = 0
    partial_refresh_limit = 20

    # Define regions for partial updates
    cpu_area = (bar_x, header_height + 27, value_x + 40, header_height + 47)
    root_area = (bar_x, header_height + 52, value_x + 40, header_height + 72)
    bkp_area = (bar_x, header_height + 77, value_x + 40, header_height + 97)
    imm_area = (bar_x, header_height + 102, value_x + 40, header_height + 122)

    # Additional areas for Temp and Net
    temp_below_area = (bar_x, header_height + 127, value_x + 40, header_height + 147)
    net_below_area = (bar_x, header_height + 152, value_x + 80, header_height + 172)  # Increased width for MB/s

    while True:
        stats = get_system_stats()

        backup_status = read_backup_status()
        # Update backup status at the bottom
        draw.rectangle((label_x, backup_status_y, epd.width, backup_status_y + 20), fill=0)
        draw.text((label_x, backup_status_y), backup_status, font=font_small, fill=255)

        if partial_refresh_count < partial_refresh_limit:
            epd.display_Partial(epd.getbuffer(image))
            partial_refresh_count += 1
        else:
            # Perform a full refresh
            epd.display(epd.getbuffer(image))
            partial_refresh_count = 0

        # Update CPU Bar and Value
        draw.rectangle(cpu_area, fill=0)  # Clear previous value
        draw_dithered_bar(draw, bar_x, cpu_area[1] + 3, bar_width, 12, stats["CPU"])
        draw.rectangle((value_x, cpu_area[1], value_x + 50, cpu_area[3]), fill=0)  # Clear previous text
        draw.text((value_x, cpu_area[1]), f"{stats['CPU']}%", font=font_small, fill=255)
        epd.display_Partial(epd.getbuffer(image))  # Corrected method name

        # Update Root Disk Bar and Value
        used, total = stats["RootDisk"]
        disk_usage = (used / total) * 100
        draw.rectangle(root_area, fill=0)  # Clear previous value
        draw_dithered_bar(draw, bar_x, root_area[1] + 3, bar_width, 12, disk_usage)
        draw.rectangle((value_x, root_area[1], value_x + 80, root_area[3]), fill=0)  # Clear previous text
        draw.text((value_x, root_area[1]), f"{used}/{total} GB", font=font_small, fill=255)
        epd.display_Partial(epd.getbuffer(image))  # Corrected method name

        # Update BK0 Bar and Value
        used, total = stats["BK0"]
        disk_usage = (used / total) * 100
        draw.rectangle(bkp_area, fill=0)  # Clear previous value
        draw_dithered_bar(draw, bar_x, bkp_area[1] + 3, bar_width, 12, disk_usage)
        draw.rectangle((value_x, bkp_area[1], value_x + 80, bkp_area[3]), fill=0)  # Clear previous text
        draw.text((value_x, bkp_area[1]), f"{used}/{total} GB", font=font_small, fill=255)
        epd.display_Partial(epd.getbuffer(image))  # Corrected method name

        # Update BK1 Bar and Value
        used, total = stats["BK1"]
        disk_usage = (used / total) * 100
        draw.rectangle(imm_area, fill=0)  # Clear previous value
        draw_dithered_bar(draw, bar_x, imm_area[1] + 3, bar_width, 12, disk_usage)
        draw.rectangle((value_x, imm_area[1], value_x + 80, imm_area[3]), fill=0)  # Clear previous text
        draw.text((value_x, imm_area[1]), f"{used}/{total} GB", font=font_small, fill=255)
        epd.display_Partial(epd.getbuffer(image))  # Corrected method name

        # Update Temperature below IMM
        draw.rectangle(temp_below_area, fill=0)  # Clear previous value
        draw.text((value_x, temp_below_area[1]), stats["Temp"], font=font_mono, fill=255)
        epd.display_Partial(epd.getbuffer(image))  # Corrected method name

        # Update Network Load below IMM
        draw.rectangle(net_below_area, fill=0)  # Clear previous value
        draw.text((value_x, net_below_area[1]), stats["Network"], font=font_mono, fill=255)
        epd.display_Partial(epd.getbuffer(image))  # Corrected method name

        time.sleep(30)  # Update every 30 seconds

def main():
    epd = epd4in2_V2.EPD()
    epd.init()

    try:
        logging.info("Updating display with system stats...")
        display_stats(epd)
    except KeyboardInterrupt:
        logging.info("Exiting...")
        epd.sleep()

if __name__ == "__main__":
    main() 