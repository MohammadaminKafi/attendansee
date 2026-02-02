import React from 'react';
import { Modal } from './Modal';
import { Button } from './Button';
import { AlertTriangle } from 'lucide-react';

interface ConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  isDestructive?: boolean;
  isProcessing?: boolean;
}

export const ConfirmationModal: React.FC<ConfirmationModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  isDestructive = false,
  isProcessing = false,
}) => {
  return (
    <Modal isOpen={isOpen} onClose={onClose} title="">
      <div className="space-y-4">
        {/* Icon and Title */}
        <div className="flex items-center gap-3">
          <div className={`p-3 rounded-full ${isDestructive ? 'bg-danger/20' : 'bg-warning/20'}`}>
            <AlertTriangle className={`w-6 h-6 ${isDestructive ? 'text-danger' : 'text-warning'}`} />
          </div>
          <h3 className="text-xl font-semibold text-white">{title}</h3>
        </div>

        {/* Message */}
        <div className="text-gray-300 leading-relaxed">
          {message}
        </div>

        {/* Actions */}
        <div className="flex gap-3 pt-4">
          <Button
            variant="secondary"
            onClick={onClose}
            disabled={isProcessing}
            className="flex-1"
          >
            {cancelText}
          </Button>
          <Button
            onClick={onConfirm}
            disabled={isProcessing}
            className={`flex-1 ${
              isDestructive
                ? 'bg-danger hover:bg-danger-dark'
                : ''
            }`}
          >
            {isProcessing ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                Processing...
              </>
            ) : (
              confirmText
            )}
          </Button>
        </div>
      </div>
    </Modal>
  );
};
