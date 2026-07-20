type SuccessAlertProps = {
  message: string;
};

export function SuccessAlert({ message }: SuccessAlertProps) {
  if (!message) {
    return null;
  }

  return (
    <div className="alert alert--success" role="status">
      {message}
    </div>
  );
}
