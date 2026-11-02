import { FieldWorkspace } from "@/components/field/field-workspace";

interface FieldPageProps {
  readonly params: Promise<{ projectId: string }>;
}

export default async function FieldPage({ params }: FieldPageProps) {
  const { projectId } = await params;
  return <FieldWorkspace projectId={projectId} />;
}
