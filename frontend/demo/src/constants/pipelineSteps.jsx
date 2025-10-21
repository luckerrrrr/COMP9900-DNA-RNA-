// Pipeline steps configuration
export const PIPELINE_STEPS = [
  { id: 1, title: "Data", subtitle: "Preprocessing", icon: "📊" },
  { id: 2, title: "MSA", subtitle: "Alignment", icon: "🧬" },
  { id: 3, title: "Token", subtitle: "Encoding", icon: "🔢" },
  { id: 4, title: "Embed", subtitle: "Vectors", icon: "📈" },
  { id: 5, title: "Predict", subtitle: "Model", icon: "🎯" },
  { id: 6, title: "Eval", subtitle: "Results", icon: "✅" },
];

// Step descriptions
export const STEP_DESCRIPTIONS = {
  1: "Data preprocessing involves cleaning DNA sequences and splitting them into 512bp windows for analysis.",
  2: "Multiple Sequence Alignment (MSA) aligns DNA from different species to identify conserved regions.",
  3: "Tokenisation converts DNA bases (A, T, C, G) into numerical representations for the model.",
  4: "Embedding transforms token sequences into high-dimensional vectors that capture biological patterns.",
  5: "The prediction model uses masked language modeling to predict missing bases in sequences.",
  6: "Evaluation uses UMAP clustering and accuracy metrics to assess model performance.",
};
