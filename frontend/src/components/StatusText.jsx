export default function StatusText({ status }) {
  return (
    <div className="text-center">
      <div className="ui-text text-gray-700 text-xl font-medium">
        {status === "idle" && "Click to start our conversation"}
        {status === "playing_prompt" && "Listening..."}
        {status === "ready_record" && "I'm ready to listen"}
        {status === "recording" && "I'm listening..."}
        {status === "uploading" && "Processing your message..."}
      </div>
      {status === "idle" && (
        <p className="body-copy text-gray-500 text-sm mt-2">
          Tap the microphone and speak naturally
        </p>
      )}
    </div>
  );
}
