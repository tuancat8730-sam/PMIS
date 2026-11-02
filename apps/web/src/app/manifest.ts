import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "PMIS Hiện trường",
    short_name: "PMIS",
    description: "Ghi nhận giao nhận thiết bị tại điểm trường, hoạt động cả khi mất mạng",
    start_url: "/field",
    scope: "/",
    display: "standalone",
    orientation: "portrait",
    background_color: "#ffffff",
    theme_color: "#0d4e8c",
    lang: "vi-VN",
    icons: [
      { src: "/icons/icon-192.png", sizes: "192x192", type: "image/png" },
      { src: "/icons/icon-512.png", sizes: "512x512", type: "image/png" },
    ],
  };
}
