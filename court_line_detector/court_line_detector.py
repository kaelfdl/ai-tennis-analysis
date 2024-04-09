import torch
import torchvision.transforms as transforms
import torchvision.models as models
import cv2

class CourtLineDetector:
    def __init__(self, model_path):
        self.model = models.resnet50(pretrained=True)
        self.model.fc = torch.nn.Linear(self.model.fc.in_features, 14 * 2)
        self.model.load_state_dict(torch.load(model_path, map_location='cpu'))

        self.transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

    def predict(self, img):
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_tensor = self.transform(img_rgb).unsqueeze(0)

        with torch.no_grad():
            outputs = self.model(img_tensor)

        kps = outputs.squeeze().cpu().numpy()

        orig_h, orig_w = img_rgb.shape[:2]

        kps[::2] *= orig_w / 224.0
        kps[1::2] *= orig_h / 224.0

        return kps

    def draw_kps(self, img, kps):
        for i in range(0, len(kps), 2):
            x = int(kps[i])
            y = int(kps[i+1])
            
            cv2.putText(img, str(i//2), (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            cv2.circle(img, (x, y), 5, (0, 0, 255), -1)

        return img
    
    def draw_kps_on_video(self, video_frames, kps):
        output_video_frames = []
        for frame in video_frames:
            frame = self.draw_kps(frame, kps)
            output_video_frames.append(frame)
        return output_video_frames


