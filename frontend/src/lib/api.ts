const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Lead {
    id?: string;
    company_name: string;
    website: string;
    email: string;
    phone: string;
    linkedin: string;
    score: number;
    grade: "Hot" | "Warm" | "Cold";
    insights: string;
    has_hiring_page: boolean;
    has_pricing_page: boolean;
    has_blog: boolean;
    blog_updated_recently: boolean;
    tech_stack: string[];
    services: string;
    created_at?: string;
}

export interface Project {
    id: string;
    name: string;
    keyword: string;
    country: string;
    status: string;
    total_leads: number;
    created_at?: string;
}

export interface Stats {
    total_projects: number;
    total_leads: number;
    hot_leads: number;
    warm_leads: number;
    cold_leads: number;
    avg_score: number;
}

export interface GenerateRequest {
    keyword: string;
    country: string;
    max_results: number;
    company_size?: string;
    project_name?: string;
}

// --- API Functions ---

export async function generateLeads(req: GenerateRequest) {
    const res = await fetch(`${API_BASE}/api/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(req),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
}

export async function getGenerationStatus(projectId: string) {
    const res = await fetch(`${API_BASE}/api/generate/${projectId}/status`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
}

export async function getProjects(): Promise<{ projects: Project[] }> {
    const res = await fetch(`${API_BASE}/api/projects`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
}

export async function getProject(id: string): Promise<Project> {
    const res = await fetch(`${API_BASE}/api/projects/${id}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
}

export async function getProjectLeads(
    projectId: string,
    grade?: string,
    minScore?: number
): Promise<{ leads: Lead[]; total: number }> {
    const params = new URLSearchParams();
    if (grade) params.set("grade", grade);
    if (minScore !== undefined) params.set("min_score", String(minScore));
    const qs = params.toString() ? `?${params.toString()}` : "";
    const res = await fetch(`${API_BASE}/api/projects/${projectId}/leads${qs}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
}

export async function getStats(): Promise<Stats> {
    const res = await fetch(`${API_BASE}/api/stats`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
}

export async function exportLeads(projectId: string) {
    const res = await fetch(`${API_BASE}/api/export`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ project_id: projectId, format: "csv" }),
    });
    if (!res.ok) throw new Error(await res.text());
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `leads_${projectId}.csv`;
    a.click();
    URL.revokeObjectURL(url);
}

export async function testPipeline(req: GenerateRequest) {
    const res = await fetch(`${API_BASE}/api/test-pipeline`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(req),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
}
