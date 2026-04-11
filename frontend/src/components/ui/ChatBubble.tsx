import { FileText, Shield, Scale, Info } from "lucide-react";

interface ChatBubbleProps {
  role: "user" | "assistant";
  content: string;
  language?: string;
}

export const ChatBubble = ({ role, content, language }: ChatBubbleProps) => {
  const isAssistant = role === "assistant";

  const renderContent = () => {
    // Try to parse JSON if it's from the assistant
    if (isAssistant) {
      try {
        const data = JSON.parse(content);
        
        return (
          <div className="space-y-4">
            {/* Main Answer Text */}
            <p className="text-sm leading-relaxed text-gray-800 font-body">
              {data.answer}
            </p>

            {/* Obligations Section */}
            {data.obligations?.length > 0 && (
              <div className="bg-primary/5 rounded-2xl p-4 border border-primary/10">
                <div className="flex items-center gap-2 mb-2">
                  <Scale size={14} className="text-primary" />
                  <span className="text-[10px] font-black uppercase tracking-widest text-primary">Key Obligations</span>
                </div>
                <div className="space-y-3">
                  {data.obligations.map((ob: any, i: number) => (
                    <div key={i} className="flex flex-col border-b border-primary/5 pb-2 last:border-0">
                      <span className="text-xs font-bold text-gray-700">{ob.obligation}</span>
                      <div className="flex justify-between items-center mt-1">
                        <span className="text-[10px] text-gray-500 italic">{ob.condition}</span>
                        <span className="text-[10px] bg-white px-2 py-0.5 rounded border font-bold text-primary">{ob.party}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        );
      } catch (e) {
        // Not JSON, render as plain text
        return <p className="text-sm leading-relaxed">{content}</p>;
      }
    }

    // User message style
    return <p className="text-sm">{content}</p>;
  };

  return (
    <div className={`max-w-[85%] p-5 rounded-3xl ${
      isAssistant 
        ? "bg-white border border-gray-100 shadow-card rounded-tl-none text-gray-800" 
        : "bg-gradient-wakili text-white shadow-lg shadow-primary/20 rounded-tr-none"
    }`}>
      {renderContent()}
    </div>
  );
};