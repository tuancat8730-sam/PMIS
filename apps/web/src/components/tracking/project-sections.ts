export interface ProjectSection {
  label: string;
  description: string;
  /** Đường dẫn con sau /projects/{id}/, có thể kèm anchor. */
  path: string;
}

/** Tổng quan đứng đầu, sau đó là sáu màn theo sheet Excel; dùng cho trang chủ và dải tab. */
export const PROJECT_SECTIONS: readonly ProjectSection[] = [
  { label: "Tổng quan", description: "Thông tin chung của dự án", path: "overview" },
  { label: "Mốc", description: "Kế hoạch và tiến độ nghiệm thu", path: "schedule" },
  { label: "Rủi ro", description: "Rủi ro và vấn đề đang theo dõi", path: "risks" },
  { label: "Pháp lý", description: "Hồ sơ pháp lý theo giai đoạn", path: "legal" },
  { label: "File", description: "Danh mục file và bằng chứng", path: "files" },
  { label: "Tệp Drive", description: "File Drive của dự án, xem trực tiếp", path: "drive" },
  { label: "Quyết định", description: "Quyết định phê duyệt của dự án", path: "decisions" },
  { label: "Hợp đồng", description: "Ma trận hợp đồng và giá trị", path: "contracts" },
];
