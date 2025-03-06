import logging
import time
import psutil
import os
import subprocess
from waveshare_epd import epd4in2_V2
from PIL import Image, ImageDraw, ImageFont

logging.basicConfig(level=logging.INFO)

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
    net_io = psutil.net_io_counters()
    net_load = (net_io.bytes_sent + net_io.bytes_recv) / 1024 / 1024  # Convert to MB

    cpu_usage = psutil.cpu_percent(interval=1)
    temp = get_cpu_temperature()
    root_used, root_total = get_disk_usage("/")
    nvme0_used, nvme0_total = get_disk_usage("/mnt/nvme0")
    nvme1_used, nvme1_total = get_disk_usage("/mnt/nvme1")

    return {
        "Network": f"{net_load:.2f} MB",
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

    # Load fonts
    header_font_path = "/usr/local/share/fonts/DotMatrixTwoExtended.ttf"  # Header font
    body_font_path = "/usr/local/share/fonts/TTF/Perfect_DOS_VGA_437.ttf"

    font_large = ImageFont.truetype(header_font_path, 28)  
    font_small = ImageFont.truetype(body_font_path, 18)  
    font_mono = ImageFont.truetype(body_font_path, 18)

    # Draw static elements (header and labels)
    header_text = "SnapSync"
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
    for label in ["[CPU]", "[ROOT]", "[BKP]", "[IMM]"]:
        draw.text((label_x, y_offset), label, font=font_small, fill=255)
        y_offset += 25

    # Labels for TEMP and NET (below IMM)
    draw.text((label_x, y_offset), "[TEMP]", font=font_small, fill=255)
    y_offset += 25
    draw.text((label_x, y_offset), "[NET]", font=font_small, fill=255)

    # Backup schedule text (static, placed at the bottom)
    backup_text = "[BKP]: 07/02 00:12 -> 14/02 00:00"
    immutable_text = "[IMM]: 01/02 00:15 -> 01/03 00:00"
    y_offset += 45  # Add some vertical spacing before the backup schedule
    draw.text((label_x, y_offset), backup_text, font=font_small, fill=255)
    y_offset += 25
    draw.text((label_x, y_offset), immutable_text, font=font_small, fill=255)

    # Full display update for static elements
    epd.display(epd.getbuffer(image))
    epd.init()  # Re-initialize for partial updates

    # Define regions for partial updates
    cpu_area = (bar_x, header_height + 27, value_x + 40, header_height + 47)
    root_area = (bar_x, header_height + 52, value_x + 40, header_height + 72)
    bkp_area = (bar_x, header_height + 77, value_x + 40, header_height + 97)
    imm_area = (bar_x, header_height + 102, value_x + 40, header_height + 122)

    # Additional areas for Temp and Net below IMM
    temp_below_area = (bar_x, header_height + 127, value_x + 40, header_height + 147)
    net_below_area = (bar_x, header_height + 152, value_x + 40, header_height + 172)

    while True:
        stats = get_system_stats()

        # Update CPU Bar and Value
        draw.rectangle(cpu_area, fill=0)  # Clear previous value
        draw_dithered_bar(draw, bar_x, cpu_area[1] + 3, bar_width, 12, stats["CPU"])
        draw.text((value_x, cpu_area[1]), f"{stats['CPU']}%", font=font_small, fill=255)
        epd.display_Partial(epd.getbuffer(image))  # Corrected method name

        # Update Root Disk Bar and Value
        used, total = stats["RootDisk"]
        disk_usage = (used / total) * 100
        draw.rectangle(root_area, fill=0)  # Clear previous value
        draw_dithered_bar(draw, bar_x, root_area[1] + 3, bar_width, 12, disk_usage)
        draw.text((value_x, root_area[1]), f"{used}/{total} GB", font=font_small, fill=255)
        epd.display_Partial(epd.getbuffer(image))  # Corrected method name

        # Update BK0 Bar and Value
        used, total = stats["BK0"]
        disk_usage = (used / total) * 100
        draw.rectangle(bkp_area, fill=0)  # Clear previous value
        draw_dithered_bar(draw, bar_x, bkp_area[1] + 3, bar_width, 12, disk_usage)
        draw.text((value_x, bkp_area[1]), f"{used}/{total} GB", font=font_small, fill=255)
        epd.display_Partial(epd.getbuffer(image))  # Corrected method name

        # Update BK1 Bar and Value
        used, total = stats["BK1"]
        disk_usage = (used / total) * 100
        draw.rectangle(imm_area, fill=0)  # Clear previous value
        draw_dithered_bar(draw, bar_x, imm_area[1] + 3, bar_width, 12, disk_usage)
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
