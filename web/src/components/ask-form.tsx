import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function AskForm({ defaultValue = "" }: { defaultValue?: string }) {
  return (
    <form action="/answer" method="get" className="flex gap-2" role="search">
      <Input
        name="q"
        defaultValue={defaultValue}
        required
        placeholder="Ask about a 10-K or 10-Q, e.g. Apple's inventories at fiscal 2024 year end"
        aria-label="Question"
        className="flex-1"
      />
      <Button type="submit">Ask</Button>
    </form>
  );
}
