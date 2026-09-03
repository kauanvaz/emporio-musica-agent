from dotenv import load_dotenv

from src.agent import interact_with_agent

load_dotenv()


def run_interactive():
    print("Digite sua mensagem: ")
    while True:
        try:
            question = input("Você: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nAté logo!")
            break
        if not question:
            continue
        try:
            answer = interact_with_agent(question)
            print(f"\nAssistente: {answer}\n")
        except Exception as exc:
            print(f"\n[erro] {exc}\n")


if __name__ == "__main__":
    run_interactive()
