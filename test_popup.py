import tkinter as tk

def create_list_popup():
    root = tk.Tk()
    root.withdraw()

    top = tk.Toplevel(root)
    top.title("Watch List")
    top.geometry("400x300")
    top.configure(bg="#121212")

    tk.Label(top, text="WATCH LIST", font=("Courier New", 18, "bold"), bg="#121212", fg="#4a90e2").pack(pady=15)
    
    container = tk.Frame(top, bg="#121212")
    container.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    data_list = [{"id": "1", "t": "Test", "y": "2020"}]

    canvas = tk.Canvas(container, bg="#121212", highlightthickness=0)
    scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg="#121212")

    canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    
    def configure_scroll_region(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
        
    def configure_window_size(event):
        canvas.itemconfig(canvas_window, width=canvas.winfo_width())

    scrollable_frame.bind("<Configure>", configure_scroll_region)
    canvas.bind("<Configure>", configure_window_size)
    
    canvas.configure(yscrollcommand=scrollbar.set)
    
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    for item in data_list:
        row = tk.Frame(scrollable_frame, bg="#1a1a1a")
        row.pack(fill="x", pady=2)
        lbl = tk.Label(row, text=f"{item['t']} ({item['y']})")
        lbl.pack(side="left")

    root.after(1000, root.destroy)
    root.mainloop()

create_list_popup()
