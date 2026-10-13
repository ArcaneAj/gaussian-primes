from gaussian_primes.generate_grid import animate, create_video_from_frames


def main() -> None:
    print("Hello from gaussian-primes!")
    animate(max_radius=100, spacing=5)
    create_video_from_frames(fps=30)
