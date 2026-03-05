export function ogTemplate(title: string, description: string, tags: string[] = []) {
  return {
    type: "div",
    props: {
      style: {
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        width: "100%",
        height: "100%",
        padding: "60px",
        background: "linear-gradient(135deg, #0a0a0a 0%, #111827 50%, #0a0a0a 100%)",
        fontFamily: "Inter",
      },
      children: [
        {
          type: "div",
          props: {
            style: { display: "flex", flexDirection: "column", gap: "16px" },
            children: [
              {
                type: "div",
                props: {
                  style: {
                    fontSize: "48px",
                    fontWeight: 700,
                    color: "#fafafa",
                    lineHeight: 1.2,
                    maxWidth: "900px",
                  },
                  children: title,
                },
              },
              {
                type: "div",
                props: {
                  style: {
                    fontSize: "22px",
                    color: "#a3a3a3",
                    lineHeight: 1.5,
                    maxWidth: "800px",
                  },
                  children: description,
                },
              },
            ],
          },
        },
        {
          type: "div",
          props: {
            style: {
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            },
            children: [
              {
                type: "div",
                props: {
                  style: { fontSize: "20px", color: "#3b82f6", fontWeight: 600 },
                  children: "shifatsanto.dev",
                },
              },
              tags.length > 0
                ? {
                    type: "div",
                    props: {
                      style: { display: "flex", gap: "8px" },
                      children: tags.slice(0, 3).map((tag) => ({
                        type: "div",
                        props: {
                          style: {
                            fontSize: "16px",
                            color: "#a3a3a3",
                            background: "#1a1a1a",
                            padding: "4px 12px",
                            borderRadius: "9999px",
                          },
                          children: tag,
                        },
                      })),
                    },
                  }
                : null,
            ],
          },
        },
      ],
    },
  };
}
