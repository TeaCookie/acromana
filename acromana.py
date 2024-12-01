from collections import defaultdict
import random
import threading
import tkinter as tk
from queue import Queue
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np

cycle = defaultdict(Queue)
end = 0
perfect = False

def delay():
  if perfect:
    return 0
  return random.randint(1, 4)

def lacerate(start, hits = 6):
  while start < end:
    duration_end = start + hits
    for i in range(start, duration_end):
      cycle[start].put("lacerate")
      start += 2
    start += delay()
  
def multihit(start, hits = 12):
  while start < end:
    duration_end = start + hits
    for i in range(start, duration_end):
      cycle[start].put("multihit")
      start += 2
    start += delay()

# for clarity, smoke is only added once, but the old system will simply multiply it by 3
def smoke(start, hits = 10):
  while start < end:
    duration_end = start + hits
    for i in range(start, duration_end):
      cycle[start].put("smoke")
      start += 10
    start += delay()

# bloom is added every 6 ticks, 
# however it supposed to proc every 0.3 seconds, 
# meaning 2 extra ticks are produced every 20 ticks -> 6 * 3 = 18, 20-18 = 2
def bloom(start):
  extra_ticks = 0
  while start < end:
    # thus every 3 hits we add 2 extra ticks
    for i in range(start, start + 3):
      cycle[start].put("bloom")
      start += 6
    extra_ticks += 2
    # if we have 6 extra ticks, we add a bloom
    if extra_ticks == 6:
      cycle[start-5].put("bloom")
      extra_ticks = 0

# Should start threads which will insert whether or not a spell hits on the specific tick
# Cycle consists of a list of lists, each list being a tick containing which spells hit on that tick
# Cycle = [[lacerate, multihit, bloom],[smoke],[lacerate, multihit],[],[],[]]
# if Perfect = True, then the delay between the same spells is 0, otherwise it is random between 0 and 3
def generate_cycle():
  threads = []
  threads.append(threading.Thread(target=lacerate, args=(0,)))
  threads.append(threading.Thread(target=multihit, args=(6+delay(),)))
  threads.append(threading.Thread(target=smoke, args=(delay(),)))
  threads.append(threading.Thread(target=bloom, args=(0,)))

  for thread in threads:
    thread.start()

  for thread in threads:
    thread.join()

  return {tick: list(q.queue) for tick, q in sorted(cycle.items())}

# for every tick in cycle, count the number of spells that hit and put the mana gained in a new list for analysis
def old_generate_cycle():
  mana_gained = defaultdict(int)
  for tick in range(max(cycle.keys()) + 1):  # Initialize all ticks to zero
    mana_gained[tick] = 0
  for tick in cycle:
    mana = cycle[tick].qsize() * 0.6
    if "smoke" in cycle[tick].queue:
      mana += 0.6 * 2
    mana_gained[tick] = round(mana, 2)
  return {tick: mana for tick, mana in sorted(mana_gained.items())}

# the new system gives 1.2 mana per tick if a hit occurs at all.
def new_generate_cycle():
  mana_gained = defaultdict(int)
  for tick in range(max(cycle.keys()) + 1):  # Initialize all ticks to zero
    mana_gained[tick] = 0
  for tick in cycle:
    mana = 1.2 if cycle[tick].qsize() > 0 else 0
    mana_gained[tick] = round(mana, 2)
  return {tick: mana for tick, mana in sorted(mana_gained.items())}
    

# Tkinter UI Visualization
def display_cycle_ui(cycle_data, new_mana_gained, old_mana_gained, max_columns=20):
    root = tk.Tk()
    root.title("Cycle Visualization")

    # Create a scrollable frame setup with canvas
    container = tk.Frame(root)
    container.pack(fill="both", expand=True)

    canvas = tk.Canvas(container)
    scrollbar_y = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
    scrollbar_x = tk.Scrollbar(container, orient="horizontal", command=canvas.xview)

    scrollable_frame = tk.Frame(canvas)
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

    scrollbar_y.pack(side="right", fill="y")
    scrollbar_x.pack(side="bottom", fill="x")
    canvas.pack(side="left", fill="both", expand=True)

    # Color map for each spell type
    color_map = {
        "lacerate": "lightcoral",
        "multihit": "lightyellow",
        "smoke": "lightgrey",
        "bloom": "lightblue"
    }

    # Determine the maximum number of spells in any tick for consistent row height
    max_spells = max(len(spells) for spells in cycle_data.values())
    max_tick = max(cycle_data.keys())

    # Display columns by tick numbers and small squares for spells
    for tick in range(max_tick + 1):
        # Calculate row and column position with wrapping
        row_offset = (tick // max_columns) * (max_spells + 3)  # Adjusted for mana label
        column_position = tick % max_columns

        # Display tick number as the header for each column
        tick_label = tk.Label(scrollable_frame, text=str(tick + 1), font=("Arial", 10, "bold"), width=4)
        tick_label.grid(row=row_offset, column=column_position, padx=5, pady=2)  # Reduced vertical padding for more space

        # Fetch spells for the tick, defaulting to an empty list if none exist
        spells = cycle_data.get(tick, [])

        # Display a small square for each spell based on color coding
        for i, spell in enumerate(spells):
            spell_color = color_map.get(spell, "white")  # Default to white if spell is not in color_map
            spell_square = tk.Label(scrollable_frame, bg=spell_color, borderwidth=1, relief="solid", width=2, height=1)
            spell_square.grid(row=row_offset + i + 1, column=column_position, padx=5, pady=2)

        # Add empty rows for consistent height in each wrapped column
        for i in range(len(spells), max_spells):
            empty_label = tk.Label(scrollable_frame, text="", width=2, height=1)
            empty_label.grid(row=row_offset + i + 1, column=column_position, padx=5, pady=2)

         # Display old system mana gained below the spells stack
        old_mana_label = tk.Label(
            scrollable_frame, text=f"{old_mana_gained.get(tick, 0):.2f}", font=("Arial", 8), fg="blue"
        )
        old_mana_label.grid(row=row_offset + max_spells + 1, column=column_position, padx=5, pady=2)  # Positioned below spells

        # Display new system mana gained below the old system mana label
        new_mana_label = tk.Label(
            scrollable_frame, text=f"{new_mana_gained.get(tick, 0):.2f}", font=("Arial", 8), fg="purple"
        )
        new_mana_label.grid(row=row_offset + max_spells + 2, column=column_position, padx=5, pady=2)  # Positioned below old mana

    # Add a color-coded key with small squares for each spell
    key_row = row_offset + max_spells + 3
    tk.Label(scrollable_frame, text="Key:", font=("Arial", 10, "bold")).grid(row=key_row, column=0, sticky="w", padx=5, pady=5)

    for i, (spell, color) in enumerate(color_map.items()):
        key_square = tk.Label(scrollable_frame, bg=color, borderwidth=1, relief="solid", width=2, height=1)
        key_square.grid(row=key_row, column=i + 1, padx=5, pady=2)  # Adjusted vertical padding
        key_label = tk.Label(scrollable_frame, text=spell, font=("Arial", 10))
        key_label.grid(row=key_row + 1, column=i + 1, padx=5, pady=2)

    root.mainloop()

def display_mana_comparison(old_mana_ticks, new_mana_ticks, tick_interval=50):
    """
    Display a dynamic bar graph comparing mana gain per tick between old and new systems.

    Parameters:
    - old_mana_ticks: List of mana gained per tick for the old system.
    - new_mana_ticks: List of mana gained per tick for the new system.
    - tick_interval: Update interval for each tick in milliseconds (default is 50 ms).
    """
    # Initialize cumulative mana trackers
    old_total_mana = 0
    new_total_mana = 0

    # Set up the figure and axis for the bar graph
    fig, ax = plt.subplots()
    bar_width = 0.4

    # Create two bars, initialized to zero
    old_bar = ax.bar(0, 0, bar_width, label="Old System", color="blue")
    new_bar = ax.bar(1, 0, bar_width, label="New System", color="green")

    # Set up plot limits and labels
    ax.set_ylim(0, max(max(old_mana_ticks), max(new_mana_ticks)) * 1.2)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Old System", "New System"])
    ax.set_ylabel("Mana Gained")
    ax.set_title("Dynamic Mana Gain Comparison per Tick")
    ax.legend()

    # Initialize text labels for tick mana and total mana
    old_mana_text = ax.text(0, max(old_mana_ticks) * 0.9, '', ha='center', va='center', color="black", weight="bold")
    new_mana_text = ax.text(1, max(new_mana_ticks) * 0.9, '', ha='center', va='center', color="black", weight="bold")
    old_total_text = ax.text(0, max(old_mana_ticks) * 1.15, 'Total: 0', ha='center', color="blue", weight="bold")
    new_total_text = ax.text(1, max(new_mana_ticks) * 1.15, 'Total: 0', ha='center', color="green", weight="bold")

    # Initialize a tick counter in the center of the graph
    tick_counter_text = ax.text(0.5, max(max(old_mana_ticks), max(new_mana_ticks)) * 0.6, 
                                'Tick: 0', ha='center', va='center', color="purple", weight="bold", fontsize=14)

    # Update function for the animation
    def update(num):
        nonlocal old_total_mana, new_total_mana

        # Get mana for the current tick
        old_tick_mana = old_mana_ticks[num]
        new_tick_mana = new_mana_ticks[num]

        # Update cumulative mana totals
        old_total_mana += old_tick_mana
        new_total_mana += new_tick_mana

        # Update bar heights for the current tick
        old_bar[0].set_height(old_tick_mana)
        new_bar[0].set_height(new_tick_mana)

        # Update text inside bars with current tick mana
        old_mana_text.set_text(f"{old_tick_mana}")
        new_mana_text.set_text(f"{new_tick_mana}")

        # Update total mana text labels
        old_total_text.set_text(f"Total: {round(old_total_mana, 2)}")
        new_total_text.set_text(f"Total: {round(new_total_mana, 2)}")

        tick_counter_text.set_text(f"Tick: {num + 1}")

        # Stop animation when reaching the last tick
        if num == len(old_mana_ticks) - 1:
          ani.event_source.stop()

        return old_bar, new_bar, old_mana_text, new_mana_text, old_total_text, new_total_text

    # Run the animation for each tick
    ani = animation.FuncAnimation(fig, update, frames=len(old_mana_ticks), interval=tick_interval)
    matplotlib.rcParams['animation.ffmpeg_path'] = "C:\\Users\\Basic\\Desktop\\hw\\winter\\ffmpeg-2024-10-24-git-153a6dc8fa-essentials_build\\bin\\ffmpeg.exe"
    writer = animation.FFMpegWriter(fps=20)
    ani.save("acrobat_weightless_buff.mp4", writer=writer) 
    plt.tight_layout()
    plt.show()

# Usage example assuming old_mana_ticks and new_mana_ticks are lists of mana per tick:
# display_mana_comparison(old_mana_ticks, new_mana_ticks)


def main():
  global end
  global perfect
  perfect = False
  end = 20*30
  result = generate_cycle()
  # display_cycle_ui(result, old_mana_gained=old_generate_cycle(), new_mana_gained=new_generate_cycle())
  old_mana_gained = old_generate_cycle()
  new_mana_gained = new_generate_cycle()

  # Convert dictionaries to lists of mana per tick values
  old_mana_ticks = list(old_mana_gained.values())
  new_mana_ticks = list(new_mana_gained.values())

  # Call the function to display the dynamic bar graph
  display_mana_comparison(old_mana_ticks, new_mana_ticks, tick_interval=50)
  
if __name__ == '__main__':
  main()