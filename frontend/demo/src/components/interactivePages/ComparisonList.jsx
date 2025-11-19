import { motion, AnimatePresence } from "framer-motion";

export default function ComparisonList({
  gpnRegions,
  gpnMsaRegions,
  isVisible,
}) {
  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, y: 20, height: 0 }}
          animate={{ opacity: 1, y: 0, height: "auto" }}
          exit={{ opacity: 0, y: 20, height: 0 }}
          transition={{ duration: 0.5 }}
          style={{
            marginTop: "40px",
            background: "rgba(255, 255, 255, 0.05)",
            backdropFilter: "blur(10px)",
            borderRadius: "16px",
            padding: "30px",
            border: "1px solid rgba(255, 255, 255, 0.1)",
          }}
        >
          {/* Title */}
          <h3
            style={{
              fontSize: "30px",
              fontWeight: "bold",
              color: "#64b5f6",
              marginBottom: "24px",
              margin: "0 0 24px 0",
              textAlign: "center",
            }}
          >
            GPN vs GPN-MSA: Top 10 Comparison
          </h3>

          {/* Form */}
          <div style={{ overflowX: "auto" }}>
            <table
              style={{
                width: "100%",
                borderCollapse: "collapse",
                fontSize: "14px",
              }}
            >
            
              <thead>
                <tr
                  style={{
                    borderBottom: "2px solid rgba(100, 181, 246, 0.3)",
                  }}
                >
                  <th
                    style={{
                      padding: "16px 12px",
                      textAlign: "center",
                      color: "#64b5f6",
                      fontWeight: "600",
                      fontSize: "25px",
                    }}
                  >
                    Rank
                  </th>
                  <th
                    style={{
                      padding: "16px 12px",
                      textAlign: "left",
                      color: "#64b5f6",
                      fontWeight: "600",
                      fontSize: "25px",
                    }}
                  >
                    GPN Region
                  </th>
                  <th
                    style={{
                      padding: "16px 12px",
                      textAlign: "center",
                      color: "#64b5f6",
                      fontWeight: "600",
                      fontSize: "25px",
                    }}
                  >
                    GPN Score
                  </th>
                  <th
                    style={{
                      padding: "16px 12px",
                      textAlign: "left",
                      color: "#66bb6a",
                      fontWeight: "600",
                      fontSize: "25px",
                    }}
                  >
                    GPN-MSA Region
                  </th>
                  <th
                    style={{
                      padding: "16px 12px",
                      textAlign: "center",
                      color: "#66bb6a",
                      fontWeight: "600",
                      fontSize: "25px",
                    }}
                  >
                    GPN-MSA Score
                  </th>
                </tr>
              </thead>

              <tbody>
                {gpnRegions.map((gpnRegion, index) => {
                  const gpnMsaRegion = gpnMsaRegions[index];
                  return (
                    <motion.tr
                      key={index}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                      style={{
                        borderBottom: "1px solid rgba(255, 255, 255, 0.1)",
                      }}
                    >
                      {/* Rank */}
                      <td
                        style={{
                          padding: "16px 12px",
                          textAlign: "center",
                        }}
                      >
                        <div
                          style={{
                            width: "32px",
                            height: "32px",
                            background: "rgba(100, 181, 246, 0.2)",
                            borderRadius: "50%",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            fontSize: "20px",
                            fontWeight: "bold",
                            color: "#64b5f6",
                            margin: "0 auto",
                          }}
                        >
                          {index + 1}
                        </div>
                      </td>

                      {/* GPN  */}
                      <td style={{ padding: "16px 12px" }}>
                        <div
                          style={{
                            fontSize: "20px",
                            color: "#aaa",
                            marginBottom: "4px",
                          }}
                        >
                          {gpnRegion.chr}:{gpnRegion.start.toLocaleString()}-
                          {gpnRegion.end.toLocaleString()}
                        </div>
                        <div
                          style={{
                            fontSize: "20px",
                            fontWeight: "600",
                            color: "#fff",
                          }}
                        >
                          {gpnRegion.gene}
                        </div>
                      </td>

                      {/* GPN score */}
                      <td
                        style={{
                          padding: "16px 12px",
                          textAlign: "center",
                        }}
                      >
                        <div
                          style={{
                            fontSize: "22px",
                            fontWeight: "bold",
                            color: "#64b5f6",
                            marginBottom: "4px",
                          }}
                        >
                          {(gpnRegion.predProb * 100).toFixed(1)}%
                        </div>
                        <div
                          style={{
                            fontSize: "20px",
                            color: "#888",
                          }}
                        >
                          PhastCons: {(gpnRegion.phastcons * 100).toFixed(1)}%
                        </div>
                      </td>

                      {/* GPN-MSA */}
                      <td style={{ padding: "16px 12px" }}>
                        <div
                          style={{
                            fontSize: "20px",
                            color: "#aaa",
                            marginBottom: "4px",
                          }}
                        >
                          {gpnMsaRegion.chr}:
                          {gpnMsaRegion.start.toLocaleString()}-
                          {gpnMsaRegion.end.toLocaleString()}
                        </div>
                        <div
                          style={{
                            fontSize: "20px",
                            fontWeight: "600",
                            color: "#fff",
                          }}
                        >
                          {gpnMsaRegion.gene}
                        </div>
                      </td>

                      {/* GPN-MSA score */}
                      <td
                        style={{
                          padding: "16px 12px",
                          textAlign: "center",
                        }}
                      >
                        <div
                          style={{
                            fontSize: "20px",
                            fontWeight: "bold",
                            color: "#66bb6a",
                            marginBottom: "4px",
                          }}
                        >
                          {(gpnMsaRegion.predProb * 100).toFixed(1)}%
                        </div>
                        <div
                          style={{
                            fontSize: "22px",
                            color: "#888",
                          }}
                        >
                          PhastCons: {(gpnMsaRegion.phastcons * 100).toFixed(1)}
                          %
                        </div>
                      </td>
                    </motion.tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Conclusion */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
            style={{
              marginTop: "24px",
              padding: "16px",
              background: "rgba(100, 181, 246, 0.1)",
              borderRadius: "8px",
              border: "1px solid rgba(100, 181, 246, 0.2)",
              textAlign: "center",
              color: "#aaa",
              fontSize: "22px",
            }}
          >
            💡 GPN-MSA generally shows higher conservation scores by
            incorporating multi-species alignment features
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
