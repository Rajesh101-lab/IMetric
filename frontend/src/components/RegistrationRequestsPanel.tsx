import React, { useState } from "react";
import { Check, ClipboardCheck, Mail, X } from "lucide-react";
import { ConfirmDialog } from "@/components/ConfirmDialog";
import { useRegistrationRequests, useReviewRegistrationRequest } from "@/hooks/useAuth";
import { RegistrationRequest } from "@/types";
import { formatRelativeTime } from "@/lib/format";

export const RegistrationRequestsPanel: React.FC = () => {
  const { data: requests = [], isLoading, isError } = useRegistrationRequests();
  const reviewMutation = useReviewRegistrationRequest();
  const [requestToReject, setRequestToReject] = useState<RegistrationRequest | null>(null);
  const [error, setError] = useState<string | null>(null);

  const review = async (request: RegistrationRequest, decision: "approve" | "reject") => {
    setError(null);
    try {
      await reviewMutation.mutateAsync({ requestId: request.id, decision });
      setRequestToReject(null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not review this request.");
    }
  };

  return (
    <section className="registration-requests" aria-label="Registration requests">
      <header className="registration-requests-heading">
        <div>
          <span className="eyebrow">WORKSPACE ACCESS</span>
          <h2>Pending requests <span>{requests.length}</span></h2>
        </div>
      </header>

      {error && <p className="registration-request-error" role="alert">{error}</p>}
      {isError && <p className="registration-request-error" role="alert">Could not load registration requests. Try again.</p>}
      {isLoading ? <div className="registration-requests-empty">Loading requests…</div> : requests.length === 0 ? (
        <div className="registration-requests-empty">
          <ClipboardCheck aria-hidden="true" />
          <h3>No pending requests</h3>
          <p>New registration requests will appear here.</p>
        </div>
      ) : (
        <div className="registration-request-list">
          {requests.map((request) => (
            <article className="registration-request-row" key={request.id}>
              <div className="registration-request-avatar">{request.username.slice(0, 1).toUpperCase()}</div>
              <div className="registration-request-identity">
                <strong>{request.username}</strong>
                <a href={`mailto:${request.contact_email}`}><Mail aria-hidden="true" />{request.contact_email}</a>
              </div>
              <time className="registration-request-time" dateTime={request.created_at}>{formatRelativeTime(request.created_at)}</time>
              <div className="registration-request-actions">
                <button type="button" className="app-btn" disabled={reviewMutation.isPending} onClick={() => review(request, "approve")}>
                  <Check aria-hidden="true" />Approve
                </button>
                <button type="button" className="app-btn ghost" disabled={reviewMutation.isPending} onClick={() => { setError(null); setRequestToReject(request); }}>
                  <X aria-hidden="true" />Reject
                </button>
              </div>
            </article>
          ))}
        </div>
      )}

      <ConfirmDialog
        open={!!requestToReject}
        title="Reject registration request"
        message={requestToReject ? `Reject the request for ${requestToReject.username}? Their submitted password hash will be erased.` : ""}
        busy={reviewMutation.isPending}
        error={error}
        onConfirm={() => requestToReject && review(requestToReject, "reject")}
        onCancel={() => { setError(null); setRequestToReject(null); }}
      />
    </section>
  );
};
