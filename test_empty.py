import tkinter as tk

def create_list_popup():
    root = tk.Tk()
    root.withdraw()
    top = tk.Toplevel(root)
    top.geometry("400x300")
    top.configure(bg="#121212")

    tk.Label(top, text="WATCH LIST", font=("Courier New", 18, "bold"), bg="#121212", fg="#4a90e2").pack(pady=15)
    
    container = tk.Frame(top, bg="#121212")
    container.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    tk.Label(container, text="This list is empty.", font=("Courier New", 12), bg="#121212", fg="#888888").pack(pady=40)

    root.after(1000, root.destroy)
    root.mainloop()

create_list_popup()
