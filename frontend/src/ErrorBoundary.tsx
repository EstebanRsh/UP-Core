import React from "react";

type Props = { children: React.ReactNode };
type State = { hasError: boolean; error?: unknown };

export default class ErrorBoundary extends React.Component<Props, State> {
  state: State = { hasError: false };
  static getDerivedStateFromError(error: unknown) {
    return { hasError: true, error };
  }
  componentDidCatch(error: unknown, info: unknown) {
    console.error("ErrorBoundary:", error, info);
  }
  render() {
    if (this.state.hasError) {
      return (
        <pre style={{ padding: 16, color: "#b91c1c", background: "#fef2f2" }}>
          {String(this.state.error ?? "Render error")}
        </pre>
      );
    }
    return this.props.children;
  }
}
