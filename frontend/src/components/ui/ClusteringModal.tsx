import React, { useState } from 'react';
import { Modal } from './Modal';
import { Button } from './Button';
import { AlertCircle, Users } from 'lucide-react';

export interface ClusteringOptions {
  max_clusters: number;
  force_clustering: boolean;
  similarity_threshold: number;
}

interface ClusteringModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCluster: (options: ClusteringOptions) => void;
  isProcessing: boolean;
  cropsWithoutEmbeddings?: number;
  title?: string;
  description?: string;
}

export const ClusteringModal: React.FC<ClusteringModalProps> = ({
  isOpen,
  onClose,
  onCluster,
  isProcessing,
  cropsWithoutEmbeddings = 0,
  title = 'Cluster Face Crops',
  description = 'Automatically group similar face crops into clusters and create students for each cluster.',
}) => {
  const [options, setOptions] = useState<ClusteringOptions>({
    max_clusters: 10,
    force_clustering: false,
    similarity_threshold: 0.7,
  });

  const handleCluster = () => {
    onCluster(options);
  };

  const hasMissingEmbeddings = cropsWithoutEmbeddings > 0;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title}>
      {/* Scrollable content container with max height */}
      <div className="max-h-[70vh] overflow-y-auto pr-2 -mr-2">
        <div className="space-y-3">
          <p className="text-sm text-gray-300">{description}</p>

          {/* Missing Embeddings Warning */}
          {hasMissingEmbeddings && (
            <div className="p-3 bg-warning/10 border border-warning/20 rounded-lg">
              <div className="flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-warning flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-xs text-warning font-medium">
                    {cropsWithoutEmbeddings} crop{cropsWithoutEmbeddings !== 1 ? 's' : ''} without embeddings will be ignored
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Max Clusters */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Maximum Number of Clusters
            </label>
            <div className="flex items-center gap-3">
              <input
                type="range"
                min="2"
                max="200"
                step="1"
                value={options.max_clusters}
                onChange={(e) =>
                  setOptions({ ...options, max_clusters: parseInt(e.target.value) })
                }
                className="flex-1"
              />
              <input
                type="number"
                min="2"
                max="200"
                value={options.max_clusters}
                onChange={(e) => {
                  const val = parseInt(e.target.value) || 2;
                  setOptions({ ...options, max_clusters: Math.min(200, Math.max(2, val)) });
                }}
                className="w-20 px-2 py-1 bg-dark-bg border border-dark-border rounded text-white text-sm focus:outline-none focus:border-primary"
              />
            </div>
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>2</span>
              <span>200</span>
            </div>
          </div>

          {/* Similarity Threshold */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Similarity Threshold: {options.similarity_threshold.toFixed(2)}
            </label>
            <input
              type="range"
              min="0.0"
              max="1.0"
              step="0.05"
              value={options.similarity_threshold}
              onChange={(e) =>
                setOptions({ ...options, similarity_threshold: parseFloat(e.target.value) })
              }
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>0.0 (Loose)</span>
              <span>1.0 (Strict)</span>
            </div>
          </div>

          {/* Force Clustering */}
          <div className="p-3 bg-dark-hover rounded-lg border border-dark-border">
            <div className="flex items-start gap-2">
              <input
                type="checkbox"
                id="force-clustering"
                checked={options.force_clustering}
                onChange={(e) =>
                  setOptions({ ...options, force_clustering: e.target.checked })
                }
                className="w-4 h-4 rounded border-gray-600 text-primary focus:ring-primary mt-0.5"
              />
              <div className="flex-1">
                <label htmlFor="force-clustering" className="text-sm text-gray-300 cursor-pointer font-medium">
                  Force clustering for all crops
                </label>
                <p className="text-xs text-gray-400 mt-1">
                  When disabled, crops with low similarity remain unassigned. When enabled, all crops are assigned.
                </p>
              </div>
            </div>
          </div>

          {/* Information Box - Compact */}
          <details className="p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
            <summary className="text-xs text-blue-400 font-medium cursor-pointer">
              How clustering works (click to expand)
            </summary>
            <ul className="text-xs text-blue-300 space-y-1 mt-2">
              <li>• Crops with existing students are kept separate</li>
              <li>• Only unidentified crops are clustered</li>
              <li>• New students created: Session_Name_Student_1, etc.</li>
              <li>• Crops without embeddings are ignored</li>
            </ul>
          </details>
        </div>
      </div>

      {/* Action Buttons - Outside scrollable area */}
      <div className="flex gap-3 pt-4 mt-4 border-t border-dark-border">
        <Button
          variant="secondary"
          onClick={onClose}
          className="flex-1"
          disabled={isProcessing}
        >
          Cancel
        </Button>
        <Button
          onClick={handleCluster}
          disabled={isProcessing}
          className="flex-1"
        >
          {isProcessing ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
              Clustering...
            </>
          ) : (
            <>
              <Users className="w-4 h-4 mr-2" />
              Start Clustering
            </>
          )}
        </Button>
      </div>
    </Modal>
  );
};
