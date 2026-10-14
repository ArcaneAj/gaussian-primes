import cv2
import os
import shutil
from PIL import Image

def is_prime(n: int) -> bool:
    """Helper to check if a standard integer is prime."""
    if n < 2:
        return False
    if n in (2, 3):
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True

def is_gaussian_prime(a: int, b: int) -> bool:
    """Determines if a + bi is a Gaussian prime."""
    abs_a, abs_b = abs(a), abs(b)
    if abs_a == 0:
        return abs_b % 4 == 3 and is_prime(abs_b)
    elif abs_b == 0:
        return abs_a % 4 == 3 and is_prime(abs_a)
    else:
        return is_prime(abs_a**2 + abs_b**2)

def get_shell_primes(r: int):
    """Gets all Gaussian primes on the exact square shell of radius r, sorted by distance."""
    if r == 0:
        points = [(0, 0)]
    else:
        points = []
        # Top and bottom edges
        for a in range(-r, r + 1):
            points.append((a, r))
            points.append((a, -r))
        # Left and right edges (excluding corners to avoid duplicates)
        for b in range(-r + 1, r):
            points.append((-r, b))
            points.append((r, b))
            
    # Filter for Gaussian primes and sort locally by squared Euclidean distance
    primes = [(a, b) for a, b in points if is_gaussian_prime(a, b)]
    primes.sort(key=lambda p: p[0]**2 + p[1]**2)
    return primes

def animate(max_radius=100, spacing=10, distance=1, output_dir="gaussian_frames"):
    # Dynamically size the canvas to comfortably fit the max radius
    width = height = (max_radius * 2 * spacing) + 21
    origin_x = width // 2
    origin_y = height // 2
    
    # Reset and create output directory for frames
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    # Create the base background image with a dim grid
    base_image = Image.new("RGB", (width, height), color="black")
    base_pixels = base_image.load()
    for x in range(width):
        for y in range(height):
            if (x - origin_x) % spacing == 0 and (y - origin_y) % spacing == 0:
                base_pixels[x, y] = (30, 30, 30)
                
    print(f"Generating animation frames shell-by-shell up to radius {max_radius}...")
    
    # Maintain a persistent image canvas so we only draw new shell points each step
    current_image = base_image.copy()
    current_pixels = current_image.load()

    connections_by_shell: dict[int, list[tuple[tuple[int, int], tuple[int, int]]]] = {}
    
    # Loop one iteration per integer grid radius r
    for r in range(max_radius + 1):
        connections: list[tuple[tuple[int, int], tuple[int, int]]] = []
        # 1. Get only the primes that fall on this exact integer radius shell
        shell_primes = get_shell_primes(r)
        
        # 2. Draw them onto the current canvas
        for gx, gy in shell_primes:
            px = origin_x + (gx * spacing)
            py = origin_y - (gy * spacing)
            
            if 0 <= px < width and 0 <= py < height:
                current_pixels[px, py] = (0, 255, 255)  # Cyan for Gaussian primes
                
                # Calculate which primes are within the distance threshold
                neighbourhood = get_neighbourhood((gx,gy), distance)
                toJoin = [x for x in neighbourhood if is_gaussian_prime(x[0], x[1])]
                if len(toJoin) == 0:
                    continue
                for nx, ny in toJoin:
                    connections.append(((gx,gy),(nx,ny)))
                
        connections_by_shell[r] = connections
        # 3. Save the frame with zero-padded naming (e.g., frame_0000.png)
        filename = os.path.join(output_dir, f"frame_{r:04d}.png")
        current_image.save(filename)
        
        if r % 10 == 0:
            print(f"Rendered radius r = {r}/{max_radius}...")

    print(f"Successfully generated {max_radius + 1} animation frames in the '{output_dir}' folder!")

    for connections in connections_by_shell.values():
        r += 1
        for ((gx, gy), (nx, ny)) in connections:
            draw_line(gx, gy, nx, ny, current_pixels, (255,255,0), max_radius, spacing, width, height)
            current_pixels[px, py] = (255, 255, 0)  # Yellow for joins
        filename = os.path.join(output_dir, f"frame_{r:04d}.png")
        current_image.save(filename)

def get_neighbourhood(point: tuple[int, int], distance: int) -> list[tuple[int, int]]:
    x, y = point
    return [
        (nx, ny)
        for nx in range(x - distance, x + distance + 1)
        for ny in range(y - distance, y + distance + 1)
        if (nx, ny) != point
    ]



def draw_line(
    x_start: int, 
    y_start: int, 
    x_end: int, 
    y_end: int, 
    pixels, 
    colour: tuple[int, int, int],
    max_radius: int,
    spacing: int,
    width: int,
    height: int,
):
    # 1. Find the center origin
    origin_x = width // 2
    origin_y = height // 2
    
    # 2. Convert Cartesian coordinates to pixel coordinates
    # (Note: Cartesian Y goes UP, so we subtract py)
    px_start = origin_x + (x_start * spacing)
    py_start = origin_y - (y_start * spacing)
    
    px_end = origin_x + (x_end * spacing)
    py_end = origin_y - (y_end * spacing)
    
    # 3. Bresenham's Line Algorithm
    dx = abs(px_end - px_start)
    dy = abs(py_end - py_start)
    sx = 1 if px_start < px_end else -1
    sy = 1 if py_start < py_end else -1
    err = dx - dy
    
    while True:
        # Ensure pixel is within image boundaries before drawing
        if 0 <= px_start < width and 0 <= py_start < height:
            pixels[px_start, py_start] = colour
            
        if px_start == px_end and py_start == py_end:
            break
            
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            px_start += sx
        if e2 < dx:
            err += dx
            py_start += sy

def create_video_from_frames(image_folder="gaussian_frames", video_name="gaussian_primes.mp4", fps=30):
    # Get all frame filenames from the directory
    images = [img for img in os.listdir(image_folder) if img.endswith(".png")]
    # Sort them numerically (frame_0000.png, frame_0001.png, etc.)
    images.sort()
    
    if not images:
        print("No images found in the specified folder!")
        return

    # Read the first image to get dimensions (width, height)
    first_image_path = os.path.join(image_folder, images[0])
    frame = cv2.imread(first_image_path)
    height, width, layers = frame.shape

    # Define the codec and create VideoWriter object (H.264 / MP4 format)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
    video = cv2.VideoWriter(video_name, fourcc, fps, (width, height))

    print(f"Stitching {len(images)} frames into '{video_name}' at {fps} FPS...")
    
    for image_name in images:
        img_path = os.path.join(image_folder, image_name)
        frame = cv2.imread(img_path)
        video.write(frame) # Write frame to video

    # Release the video writer
    video.release()
    cv2.destroyAllWindows()
    print(f"Video successfully saved as '{video_name}'!")

if __name__ == "__main__":
    # Run your animation generation first
    animate(max_radius=100, spacing=10)
    
    # Then compile to video (e.g., 30 frames per second)
    create_video_from_frames(fps=30)