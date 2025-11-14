# main.py
import os

proyecto = input("\nProyecto que quieres ejecutar: ")

archivo = proyecto + ".py"

if archivo in os.listdir():
    print(f"Ejecutando {archivo}...\n")
    exec(open(archivo).read())
else:
    print("Ese proyecto no existe. Intenta otra vez.")
