export default function ErrorBox({ error }) {
  if (!error) return null;
  return (
    <div className="bg-red-50 border border-red-200 rounded-2xl p-4 max-w-md mx-auto">
      <div className="text-red-700 text-center">{error}</div>
    </div>
  );
}
