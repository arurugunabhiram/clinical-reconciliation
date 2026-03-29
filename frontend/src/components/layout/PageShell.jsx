export default function PageShell({ children }) {
  return (
    <main
      className="mx-auto px-6 pt-8 pb-16"
      style={{ maxWidth: "1100px" }}
    >
      {children}
    </main>
  );
}
