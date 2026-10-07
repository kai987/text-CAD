import DownloadFile from './DownloadFile';
import type { DownloadFileProps } from './DownloadFile';

export default function StepDownload(props: Omit<DownloadFileProps, 'type' | 'compressedStep'>) {
  return <DownloadFile {...props} type="STEP" compressedStep />;
}
